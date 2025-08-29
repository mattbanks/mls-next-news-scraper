# MLS NEXT News Scraper

A robust Python-based web scraper that extracts news articles from the [MLS NEXT news page](https://www.mlssoccer.com/mlsnext/news/) and generates an RSS feed for easy consumption in feed readers.

## Features

- 🎯 **Smart Article Extraction**: Automatically identifies and extracts articles from different page sections:
  - Hero article (main featured article)
  - Sidebar articles (5 smaller articles to the right)
  - Below articles (additional articles below the main content)
- 📡 **RSS Feed Generation**: Creates a standard RSS 2.0 feed with article metadata
- 🔄 **Duplicate Prevention**: Removes duplicate articles based on title
- 📅 **Date Handling**: Extracts and parses article dates, with fallback to current time
- 🖼️ **Image Support**: Includes article images in the RSS feed when available
- 📊 **JSON Export**: Saves extracted articles to JSON for debugging and backup
- 🚀 **GitHub Actions Integration**: Automated execution every 30 minutes

## Quick Start

### GitHub Actions (Recommended)

- **Feeds**: Automatically updated every 30 minutes

### Local Execution

```bash
# Quick setup
./setup.sh

# Run scraper
./run_scraper.sh

# Or run manually
python mls_next_scraper.py
```

## Output Files

The scraper generates two output files in the `output/` directory (these are temporary and not committed):

- **`mls_next_news.xml`**: RSS feed for your feed reader
- **`mls_next_articles.json`**: JSON backup with all extracted article data

**Note**: These files are generated locally for testing and by the GitHub workflow. The actual RSS feeds are served from the `rss-feeds` branch at the URLs below.

## RSS Feed Details

The generated RSS feed includes:

- **Title**: Article headline
- **Link**: Direct link to the full article
- **Description**: Article summary/excerpt
- **Publication Date**: Article publication date
- **Image**: Article featured image (when available)

## Configuration

Edit `config.py` to customize:

- Maximum number of articles (default: 15)
- Request timeout (default: 30 seconds)
- Output file paths
- Logging level

## 📱 **Feed Access**

### **RSS Feed (for feed readers)**

Add this URL to your preferred RSS reader:

```
https://mattbanks.github.io/mls-next-news-scraper/mls_next_news.xml
```

### **JSON Feed (for developers/APIs)**

Access structured data at:

```
https://mattbanks.github.io/mls-next-news-scraper/mls_next_articles.json
```

## Troubleshooting

- **No articles**: Check website structure and internet connectivity
- **Feeds not updating**: Verify GitHub Actions are enabled
- **Local errors**: Ensure dependencies are installed and Python 3.8+
- **Debug mode**: `logging.basicConfig(level=logging.DEBUG)`

## Technical Details

- **Python 3.13+** with robust error handling
- **Dependencies**: requests, beautifulsoup4, feedgen, lxml, python-dateutil, pytz
- **Multiple fallback strategies** for website changes
- **Smart content detection** to prevent unnecessary deployments
- **Clean architecture** with separate scripts for maintainability

## Scripts

### **Content Change Detection**

The workflow uses smart content detection to only deploy when articles actually change:

```bash
# Manual content comparison
python scripts/check_content_changes.py output/mls_next_news.xml previous_file.xml
```

### **Main Scraper**

```bash
python mls_next_scraper.py
```

### **Testing**

```bash
# Test the scraper functionality locally
python test_scraper.py
```

## Contributing

Fork, make changes, test, and submit a pull request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

Check troubleshooting section, review GitHub Actions logs, or open an issue.

---

**Happy reading! ⚽📰**
