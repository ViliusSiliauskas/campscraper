"""
Configuration settings for the Vilnius summer camps scraper.
"""

# Scraping settings
MAX_CAMPS = 20  # Maximum number of camps to scrape
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds
DELAY_BETWEEN_REQUESTS = 2  # Delay between page requests in seconds

# Output settings
OUTPUT_ENCODING = "utf-8"

# URL settings
BASE_URL = "https://vilnius.lt/savivaldybe/vasaros-stovyklos"

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
}

# XPath selectors
SELECTORS = {
    "camp_cards": '//div[contains(@class, "rounded-b-2.5xl")]',
    "title": './/h3/text()',
    "organizer": './/h6[contains(text(), "Organizatorius")]',
    "age_group": './/h6[contains(text(), "Amžiaus grupė")]',
    "price": './/h6[contains(text(), "Kaina")]',
    "link": './/a/@href'
}

# CSV column names
CSV_COLUMNS = {
    "title": "Stovyklos pavadinimas",
    "organizer": "Organizatorius",
    "age_group": "Amžiaus grupė",
    "price": "Kaina",
    "link": "Nuoroda"
} 
