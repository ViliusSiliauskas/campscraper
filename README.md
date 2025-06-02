# Vilnius Summer Camps Scraper

A Python web scraper that collects information about summer camps from the Vilnius municipality website.

## Features

- Scrapes camp information including:
  - Camp name (Stovyklos pavadinimas)
  - Organizer (Organizatorius)
  - Age group (Amžiaus grupė)
  - Price (Kaina)
  - Link (Nuoroda)
- Saves data to CSV format
- Generates summary statistics
- Polite crawling with delays between requests
- Error handling and logging
- Configurable number of camps to scrape

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ViliusSiliauskas/campscraper.git
cd campscraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python src/scraper.py
```

The scraper will:
1. Collect data from the Vilnius municipality website
2. Save camp information to a CSV file in the `output` directory
3. Generate a summary report
4. Create a detailed log file

## Output Files

The scraper generates several files in the `output` directory:

- `vasaros_stovyklos_[timestamp].csv`: Main data file containing all scraped camp information
- `summary.txt`: Statistical summary including:
  - Total number of camps
  - Average price
  - Price range
  - Number of free camps
  - Number of unique organizers
- `scraper.log`: Detailed logging information about the scraping process

## Configuration

You can modify the following settings in `src/config.py`:
- `MAX_CAMPS`: Maximum number of camps to scrape
- `DELAY_BETWEEN_REQUESTS`: Time to wait between requests (in seconds)
- `REQUEST_TIMEOUT`: Maximum time to wait for each request

## Requirements

- Python 3.x
- Required packages (installed via requirements.txt):
  - requests>=2.32.3
  - beautifulsoup4>=4.12.3
  - pandas>=2.2.3
  - lxml>=5.4.0
  - python-dateutil>=2.9.0