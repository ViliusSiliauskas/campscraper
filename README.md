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
- Polite crawling with delays between requests
- Error handling and logging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd vasaros-stovyklos
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```