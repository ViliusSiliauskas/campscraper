"""
Web scraper for Vilnius summer camps data.
"""

import requests
import pandas as pd
import time
from lxml import html
from datetime import datetime
import logging
from pathlib import Path
from . import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir

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
    logging.info(f"📝 {field_name}: {value}")
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

    logging.info("🚀 Starting web scraping...")

    while len(all_camps) < max_camps:
        url = f"{config.BASE_URL}?page={page}" if page > 1 else config.BASE_URL
        logging.info(f"🔄 Loading page: {url}")

        try:
            response = requests.get(
                url, 
                headers=config.HEADERS, 
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            logging.info(f"✅ Successfully fetched page {page}")
        except requests.exceptions.RequestException as e:
            logging.error(f"🔚 Error fetching page {url}: {e}")
            break

        try:
            tree = html.fromstring(response.content)
            cards = tree.xpath(config.SELECTORS["camp_cards"])
            logging.info(f"📊 Found {len(cards)} camp cards on page {page}")
            
            if not cards:
                logging.info(f"No camp cards found on page {page}. Stopping.")
                break

            for card in cards:
                if len(all_camps) >= max_camps:
                    break

                try:
                    # Extract title
                    title_el = card.xpath(config.SELECTORS["title"])
                    title = title_el[0].strip() if title_el else "–"
                    logging.info(f"📝 Processing camp: {title}")

                    # Extract other fields
                    organizer = extract_field(card, config.SELECTORS["organizer"], "Organizatorius")
                    age = extract_field(card, config.SELECTORS["age_group"], "Amžiaus grupė")
                    price = extract_field(card, config.SELECTORS["price"], "Kaina")

                    # Extract link
                    link_el = card.xpath(config.SELECTORS["link"])
                    link = f"{config.BASE_URL}{link_el[0]}" if link_el else "–"

                    all_camps.append({
                        config.CSV_COLUMNS["title"]: title,
                        config.CSV_COLUMNS["organizer"]: organizer,
                        config.CSV_COLUMNS["age_group"]: age,
                        config.CSV_COLUMNS["price"]: price,
                        config.CSV_COLUMNS["link"]: link
                    })

                    logging.info(f"✅ Successfully processed camp {len(all_camps)} / {max_camps}")

                except Exception as e:
                    logging.error(f"⚠️ Error processing camp: {str(e)}")
                    continue

            page += 1
            time.sleep(config.DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            logging.error(f"⚠️ Error parsing page {page}: {str(e)}")
            break

    return all_camps

def save_to_csv(camps, filename=None):
    """
    Save camps data to CSV file
    
    Args:
        camps (list): List of dictionaries containing camp information
        filename (str, optional): Name of the output CSV file. 
                                If None, generates timestamped filename
    """
    try:
        output_dir = setup_output_directory()
        filename = filename or get_timestamped_filename()
        filepath = output_dir / filename

        df = pd.DataFrame(camps)
        df.to_csv(filepath, index=False, encoding=config.OUTPUT_ENCODING)
        logging.info(f"✅ Data saved to {filepath}")
        logging.info(f"📊 Total camps collected: {len(camps)}")
        
        generate_summary(df, output_dir)
        
    except Exception as e:
        logging.error(f"⚠️ Error saving to CSV: {str(e)}")

def generate_summary(df, output_dir):
    """
    Generate summary statistics about the camps
    
    Args:
        df (pandas.DataFrame): DataFrame containing camp data
        output_dir (Path): Directory to save summary
    """
    try:
        # Price analysis
        df['price_numeric'] = df['Kaina'].str.extract(r'(\d+)').astype(float)
        
        summary = {
            'total_camps': len(df),
            'avg_price': df['price_numeric'].mean(),
            'min_price': df['price_numeric'].min(),
            'max_price': df['price_numeric'].max(),
            'free_camps': len(df[df['Kaina'].str.contains('nemokama', case=False, na=False)]),
            'organizers_count': df['Organizatorius'].nunique()
        }
        
        # Save summary to file
        summary_file = output_dir / 'summary.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Summer Camps Summary\n")
            f.write("===================\n\n")
            f.write(f"Total Camps: {summary['total_camps']}\n")
            f.write(f"Average Price: {summary['avg_price']:.2f}€\n")
            f.write(f"Price Range: {summary['min_price']}€ - {summary['max_price']}€\n")
            f.write(f"Free Camps: {summary['free_camps']}\n")
            f.write(f"Unique Organizers: {summary['organizers_count']}\n")
        
        logging.info(f"✅ Summary saved to {summary_file}")
        
    except Exception as e:
        logging.error(f"⚠️ Error generating summary: {str(e)}")

def main():
    """Main function to run the scraper"""
    try:
        camps = scrape_camps()
        save_to_csv(camps)
    except Exception as e:
        logging.error(f"⚠️ Fatal error: {str(e)}")

if __name__ == "__main__":
    main() 