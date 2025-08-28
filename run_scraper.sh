#!/bin/bash

# MLS NEXT News Scraper Runner Script
# Use this script for local execution and cron jobs

# Change to the script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the scraper
echo "$(date): Starting MLS NEXT news scraper..."
python mls_next_scraper.py

# Check if successful
if [ $? -eq 0 ]; then
    echo "$(date): Scraper completed successfully"

    # Optional: Copy RSS file to a web-accessible location
    # cp output/mls_next_news.xml /var/www/html/mls_next_news.xml

    # Optional: Send notification (uncomment and modify as needed)
    # echo "MLS NEXT news updated" | mail -s "Scraper Success" your-email@example.com
else
    echo "$(date): Scraper failed with exit code $?"

    # Optional: Send failure notification
    # echo "MLS NEXT news scraper failed" | mail -s "Scraper Failure" your-email@example.com
fi
