# MLS NEXT News Scraper

A Python-based web scraper that extracts news articles from the MLS NEXT section of mlssoccer.com and generates RSS feeds.

## Features

- **Automated Scraping**: Scrapes MLS NEXT news articles automatically
- **RSS Feed Generation**: Creates standard RSS feeds for news readers
- **JSON Output**: Provides structured JSON data for programmatic access
- **Smart Change Detection**: Only deploys when content actually changes
- **URL Normalization**: Prevents false positives when MLS changes URL paths but articles remain the same
- **GitHub Actions Integration**: Automated execution every 30 minutes

## URL Normalization

The scraper now includes intelligent URL normalization to handle cases where MLS changes URL structures without changing article content. This prevents unnecessary deployments when:

- MLS redirects articles from `/allstar/2025/news/` to `/mlsnext/news/`
- MLS moves articles from `/generation-adidas-cup/news/` to `/mlsnext/news/`
- Any other URL path restructuring that doesn't change the actual article

The system extracts the article slug from URLs and normalizes them to detect when articles are the same despite different paths.

## Quick Start

### GitHub Actions (Recommended)

- **Feeds**: Automatically updated every 30 minutes
- **RSS URL**: `https://mattbanks.github.io/mls-next-news-scraper/mls_next_news.xml`
- **JSON URL**: `https://mattbanks.github.io/mls-next-news-scraper/mls_next_articles.json`

### Local Execution

```bash
# Quick setup
./setup.sh

# Run scraper
./run_scraper.sh

# Or run manually
python mls_next_scraper.py
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/mattbanks/mls-next-news-scraper.git
cd mls-next-news-scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the scraper (optional):

```bash
cp config.py.example config.py
# Edit config.py with your preferred settings
```

## Usage

### Basic Scraping

Run the scraper directly:

```bash
python mls_next_scraper.py
```

Or use the shell script:

```bash
./run_scraper.sh
```

### Change Detection

Check if content has changed:

```bash
python scripts/check_content_changes.py output/mls_next_news.xml
```

Compare with a previous version:

```bash
python scripts/check_content_changes.py output/mls_next_news.xml previous_version.xml
```

### Testing

Test URL normalization:

```bash
python scripts/test_url_normalization.py
```

Test change detection:

```bash
python scripts/test_change_detection.py
```

## Output

The scraper generates:

- `output/mls_next_news.xml` - RSS feed
- `output/mls_next_articles.json` - Structured JSON data

## Configuration

Key configuration options in `config.py`:

- `REQUEST_TIMEOUT`: HTTP request timeout (default: 30 seconds)
- `REQUEST_DELAY`: Delay between requests (default: 1 second)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `USER_AGENT`: Custom user agent string

## GitHub Actions

The repository includes GitHub Actions workflows for:

- Automated scraping and deployment
- RSS feed updates
- Content change detection with URL normalization

## Technical Details

- **Python 3.13+** with robust error handling
- **Dependencies**: requests, beautifulsoup4, feedgen, lxml, python-dateutil, pytz
- **Multiple fallback strategies** for website changes
- **Smart content detection** to prevent unnecessary deployments
- **Clean architecture** with separate scripts for maintainability

## Troubleshooting

See `TROUBLESHOOTING.md` for common issues and solutions.

## Contributing

Fork, make changes, test, and submit a pull request.

## License

This project is open source and available under the MIT License.

---

**Happy reading! ⚽📰**
