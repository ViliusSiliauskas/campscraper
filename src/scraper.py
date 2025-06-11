"""
Web scraper for Vilnius summer camps data.
"""

import requests
import pandas as pd
import numpy as np
import time
import json
from lxml import html
from datetime import datetime
import logging
from pathlib import Path
import config
import os

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    output_dir = script_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

# Set up logging with proper path
output_dir = setup_output_directory()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(output_dir / 'scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_timestamped_filename():
    """Generate filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"vasaros_stovyklos_{timestamp}.csv"

def extract_field(card, selector, field_name):
    """
    Extract a field from a camp card using XPath selector
    
    Args:
        card: HTML element containing camp data
        selector (str): XPath selector for the field
        field_name (str): Name of the field for logging
        
    Returns:
        str: Extracted field value or "–" if not found
    """
    value = "–"
    h6 = card.xpath(selector)
    if h6:
        p = h6[0].getnext()
        if p is not None and p.tag == 'p':
            value = p.text_content().strip()
    return value

def scrape_camps(max_camps=None):
    """
    Scrape summer camps data from vilnius.lt
    
    Args:
        max_camps (int, optional): Maximum number of camps to scrape. 
                                 If None, uses config.MAX_CAMPS
        
    Returns:
        list: List of dictionaries containing camp information
    """
    max_camps = max_camps or config.MAX_CAMPS
    page = 1
    all_camps = []

    logging.info("Starting web scraping...")

    while len(all_camps) < max_camps:
        url = f"{config.BASE_URL}?page={page}" if page > 1 else config.BASE_URL
        logging.info(f"Processing page {page}: {url}")

        try:
            # Fetch and parse page
            response = requests.get(
                url, 
                headers=config.HEADERS, 
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            tree = html.fromstring(response.content)
            cards = tree.xpath(config.SELECTORS["camp_cards"])
            
            if not cards:
                logging.info(f"No more camps found on page {page}. Stopping.")
                break

            # Process each card
            for card in cards:
                if len(all_camps) >= max_camps:
                    break

                # Extract all fields
                title_el = card.xpath(config.SELECTORS["title"])
                title = title_el[0].strip() if title_el else "–"
                
                camp_data = {
                    config.CSV_COLUMNS["title"]: title,
                    config.CSV_COLUMNS["organizer"]: extract_field(card, config.SELECTORS["organizer"], "Organizatorius"),
                    config.CSV_COLUMNS["age_group"]: extract_field(card, config.SELECTORS["age_group"], "Amžiaus grupė"),
                    config.CSV_COLUMNS["price"]: extract_field(card, config.SELECTORS["price"], "Kaina")
                }
                
                # Extract link
                link_el = card.xpath(config.SELECTORS["link"])
                camp_data[config.CSV_COLUMNS["link"]] = f"{config.BASE_URL}{link_el[0]}" if link_el else "–"
                
                all_camps.append(camp_data)
                logging.info(f"Processed camp {len(all_camps)}/{max_camps}: {title}")

            page += 1
            time.sleep(config.DELAY_BETWEEN_REQUESTS)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching page {url}: {str(e)}")
            break
        except Exception as e:
            logging.error(f"Error processing page {page}: {str(e)}")
            break

    logging.info(f"Completed scraping. Total camps collected: {len(all_camps)}")
    return all_camps

def analyze_prices(df):
    """
    Analyze price data using NumPy
    
    Args:
        df: DataFrame containing camp data
        
    Returns:
        dict: Price statistics and outliers
    """
    # Convert prices to numeric, handling non-numeric values
    price_array = np.array(df['price_numeric'])
    price_array = price_array[~np.isnan(price_array)]  # Remove NaN values
    
    if len(price_array) == 0:
        return {
            'mean': 0,
            'median': 0,
            'std': 0,
            'percentiles': [0, 0, 0],
            'outliers': []
        }
    
    # Calculate basic statistics
    stats = {
        'mean': float(np.mean(price_array)),
        'median': float(np.median(price_array)),
        'std': float(np.std(price_array)),
        'percentiles': [float(x) for x in np.percentile(price_array, [25, 50, 75])]
    }
    
    # Identify outliers using IQR method
    Q1, Q3 = np.percentile(price_array, [25, 75])
    IQR = Q3 - Q1
    outliers = price_array[(price_array < Q1 - 1.5*IQR) | (price_array > Q3 + 1.5*IQR)]
    stats['outliers'] = [float(x) for x in outliers]
    
    return stats

def analyze_age_groups(df):
    """
    Analyze age group data using NumPy
    
    Args:
        df: DataFrame containing camp data
        
    Returns:
        dict: Age group statistics
    """
    # Extract numeric ages from age group strings (both start and end ages)
    age_ranges = df['Amžiaus grupė'].str.extractall(r'(\d+)').astype(float)
    
    if len(age_ranges) == 0:
        return {
            'mean_age': 0,
            'age_range': {'min': 0, 'max': 0},
            'most_common_age': 0
        }
    
    # Reshape the array to handle start and end ages
    age_array = age_ranges.values.flatten()
    
    # Calculate age statistics
    age_stats = {
        'mean_age': float(np.mean(age_array)),
        'age_range': {
            'min': float(np.min(age_array)),
            'max': float(np.max(age_array))
        },
        'most_common_age': float(np.bincount(age_array.astype(int)).argmax())
    }
    
    return age_stats

def save_analysis_csv(df, output_dir):
    """
    Save price and age analysis to CSV files
    
    Args:
        df: DataFrame containing camp data
        output_dir: Path to output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Price analysis
    price_stats = analyze_prices(df)
    price_df = pd.DataFrame({
        'Metric': ['Mean Price', 'Median Price', 'Standard Deviation', 
                  'First Quartile (25%)', 'Second Quartile (50%)', 'Third Quartile (75%)'],
        'Value (EUR)': [
            price_stats['mean'],
            price_stats['median'],
            price_stats['std'],
            price_stats['percentiles'][0],
            price_stats['percentiles'][1],
            price_stats['percentiles'][2]
        ]
    })
    
    # Save outliers in a separate DataFrame
    outliers_df = pd.DataFrame({
        'Outlier Prices (EUR)': price_stats['outliers']
    })
    
    # Age analysis
    age_stats = analyze_age_groups(df)
    age_df = pd.DataFrame({
        'Metric': ['Mean Age', 'Minimum Age', 'Maximum Age', 'Most Common Age'],
        'Value (Years)': [
            age_stats['mean_age'],
            age_stats['age_range']['min'],
            age_stats['age_range']['max'],
            age_stats['most_common_age']
        ]
    })
    
    # Save DataFrames to CSV files
    price_df.to_csv(output_dir / f'price_analysis_{timestamp}.csv', index=False, encoding='utf-8-sig')
    outliers_df.to_csv(output_dir / f'price_outliers_{timestamp}.csv', index=False, encoding='utf-8-sig')
    age_df.to_csv(output_dir / f'age_analysis_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    logging.info(f"Analysis data saved to CSV files in {output_dir}")

def save_to_csv(camps, filename=None):
    """
    Save camps data to CSV file and generate summary
    
    Args:
        camps (list): List of dictionaries containing camp information
        filename (str, optional): Name of the output CSV file. 
                                If None, generates timestamped filename
    """
    if not camps:
        logging.warning("No camps data to save")
        return

    try:
        output_dir = setup_output_directory()
        filename = filename or get_timestamped_filename()
        filepath = output_dir / filename

        # Save to CSV with UTF-8-BOM encoding for Excel compatibility
        df = pd.DataFrame(camps)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logging.info(f"Data saved to {filepath}")
        
        # Extract numeric prices for analysis
        df['price_numeric'] = df['Kaina'].str.extract(r'(\d+)').astype(float)
        
        # Generate and save summary
        summary = {
            'total_camps': len(df),
            'avg_price': df['price_numeric'].mean(),
            'min_price': df['price_numeric'].min(),
            'max_price': df['price_numeric'].max(),
            'free_camps': len(df[df['Kaina'].str.contains('nemokama', case=False, na=False)]),
            'organizers_count': df['Organizatorius'].nunique()
        }
        
        summary_file = output_dir / 'summary.txt'
        with open(summary_file, 'w', encoding='utf-8-sig') as f:
            f.write("Summer Camps Summary\n")
            f.write("===================\n\n")
            f.write(f"Total Camps: {summary['total_camps']}\n")
            f.write(f"Average Price: {summary['avg_price']:.2f}€\n")
            f.write(f"Price Range: {summary['min_price']}€ - {summary['max_price']}€\n")
            f.write(f"Free Camps: {summary['free_camps']}\n")
            f.write(f"Unique Organizers: {summary['organizers_count']}\n")
        
        logging.info(f"Summary saved to {summary_file}")
        
        # Save detailed analysis to CSV files
        save_analysis_csv(df, output_dir)
        
    except Exception as e:
        logging.error(f"Error saving data: {str(e)}")

def main():
    """Main function to run the scraper"""
    try:
        camps = scrape_camps()
        save_to_csv(camps)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 