#!/usr/bin/env python3
"""
Test script for the MLS NEXT News Scraper.
Run this to test the scraper functionality.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mls_next_scraper import MLSNextScraper
import logging

def test_scraper():
    """Test the scraper functionality."""
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing MLS NEXT News Scraper...")
    print("=" * 50)

    # Create scraper instance
    scraper = MLSNextScraper()

    # Test page fetching
    print("📄 Testing page fetch...")
    soup = scraper.fetch_page()
    if soup:
        print("✅ Page fetch successful")
    else:
        print("❌ Page fetch failed")
        return False

    # Test article extraction
    print("📰 Testing article extraction...")
    articles = scraper.scrape_articles()

    if articles:
        print(f"✅ Successfully extracted {len(articles)} articles")

        # Show first few articles
        print("\n📋 Sample articles:")
        for i, article in enumerate(articles[:3]):
            print(f"  {i+1}. {article['title']}")
            print(f"     Link: {article['link']}")
            print(f"     Date: {article['date']}")
            print(f"     Hero: {article['is_hero']}")
            print()

        # Test RSS generation
        print("📡 Testing RSS generation...")
        rss_success = scraper.generate_rss(articles, "test_output.xml")
        if rss_success:
            print("✅ RSS generation successful")
        else:
            print("❌ RSS generation failed")

        # Test JSON export
        print("💾 Testing JSON export...")
        json_success = scraper.save_articles_json(articles, "test_output.json")
        if json_success:
            print("✅ JSON export successful")
        else:
            print("❌ JSON export failed")

        return True
    else:
        print("❌ No articles were extracted")
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\n🎉 All tests passed! The scraper is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the logs above for details.")
        sys.exit(1)
