#!/usr/bin/env python3
"""
MLS NEXT News Scraper
Scrapes news articles from https://www.mlssoccer.com/mlsnext/news/
and generates an RSS feed.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import pytz
from dateutil import parser
import os
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLSNextScraper:
    """Scraper for MLS NEXT news articles."""

    def __init__(self):
        self.base_url = "https://www.mlssoccer.com"
        self.news_url = f"{self.base_url}/mlsnext/news/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_page(self) -> Optional[BeautifulSoup]:
        """Fetch the news page and return BeautifulSoup object."""
        try:
            logger.info(f"Fetching page: {self.news_url}")
            response = self.session.get(self.news_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info("Page fetched successfully")
            return soup

        except requests.RequestException as e:
            logger.error(f"Failed to fetch page: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching page: {e}")
            return None

    def extract_hero_article(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract the main hero article."""
        try:
            # Look for the hero article - it's typically the largest article at the top
            hero_selectors = [
                'article[class*="hero"]',
                'div[class*="hero"] article',
                'div[class*="featured"] article',
                'div[class*="main"] article',
                'section[class*="hero"] article'
            ]

            hero_article = None
            for selector in hero_selectors:
                hero_article = soup.select_one(selector)
                if hero_article:
                    break

            if not hero_article:
                # Fallback: look for the first large article
                hero_article = soup.find('article') or soup.find('div', class_=re.compile(r'hero|featured|main'))

            if hero_article:
                return self._extract_article_data(hero_article, is_hero=True)

            return None

        except Exception as e:
            logger.error(f"Error extracting hero article: {e}")
            return None

    def extract_sidebar_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract the 5 smaller articles from the right sidebar."""
        articles = []
        try:
            # Look for sidebar articles - they're typically to the right of the hero
            sidebar_selectors = [
                'div[class*="sidebar"] article',
                'div[class*="secondary"] article',
                'div[class*="right"] article',
                'aside article',
                'div[class*="grid"] div[class*="col"]:not(:first-child) article'
            ]

            for selector in sidebar_selectors:
                sidebar_articles = soup.select(selector)
                if sidebar_articles:
                    for article in sidebar_articles[:5]:  # Limit to 5
                        article_data = self._extract_article_data(article)
                        if article_data:
                            articles.append(article_data)
                    break

            # If no sidebar articles found, try alternative approach
            if not articles:
                # Look for articles in a grid layout
                grid_articles = soup.select('div[class*="grid"] article, div[class*="row"] article')
                if len(grid_articles) > 1:
                    # Skip the first one (hero) and take the next 5
                    for article in grid_articles[1:6]:
                        article_data = self._extract_article_data(article)
                        if article_data:
                            articles.append(article_data)

            logger.info(f"Extracted {len(articles)} sidebar articles")
            return articles

        except Exception as e:
            logger.error(f"Error extracting sidebar articles: {e}")
            return []

    def extract_below_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract articles below the hero section."""
        articles = []
        try:
            # Look for articles below the main content area
            below_selectors = [
                'div[class*="below"] article',
                'div[class*="more"] article',
                'section[class*="additional"] article',
                'div[class*="list"] article',
                'div[class*="articles"] article'
            ]

            for selector in below_selectors:
                below_articles = soup.select(selector)
                if below_articles:
                    for article in below_articles:
                        article_data = self._extract_article_data(article)
                        if article_data:
                            articles.append(article_data)
                    break

            # If no specific below section found, try to get all remaining articles
            if not articles:
                all_articles = soup.find_all('article')
                # Skip the first 6 articles (hero + 5 sidebar) and take the next 10
                remaining_articles = all_articles[6:16]
                for article in remaining_articles:
                    article_data = self._extract_article_data(article)
                    if article_data:
                        articles.append(article_data)

            logger.info(f"Extracted {len(articles)} below articles")
            return articles

        except Exception as e:
            logger.error(f"Error extracting below articles: {e}")
            return []

    def _extract_article_data(self, article_element, is_hero: bool = False) -> Optional[Dict]:
        """Extract article data from a BeautifulSoup article element."""
        try:
            # Extract title
            title_elem = article_element.find(['h1', 'h2', 'h3', 'h4'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # Extract link
            link_elem = article_element.find('a')
            if not link_elem or not link_elem.get('href'):
                return None

            link = link_elem['href']
            if not link.startswith('http'):
                link = self.base_url + link

            # Extract description/summary
            description = ""
            desc_elem = article_element.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt'))
            if desc_elem:
                description = desc_elem.get_text(strip=True)

            # Extract image
            image_url = ""
            img_elem = article_element.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = self.base_url + image_url

            # Extract date (try multiple approaches)
            date = None
            date_elem = article_element.find(['time', 'span', 'div'],
                                          class_=re.compile(r'date|time|published'))
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                if date_text:
                    try:
                        date = parser.parse(date_text)
                        if date.tzinfo is None:
                            date = pytz.UTC.localize(date)
                    except:
                        pass

            # If no date found, use current time
            if not date:
                date = datetime.now(timezone.utc)

            return {
                'title': title,
                'link': link,
                'description': description,
                'image_url': image_url,
                'date': date,
                'is_hero': is_hero
            }

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None

    def scrape_articles(self) -> List[Dict]:
        """Main method to scrape all articles."""
        soup = self.fetch_page()
        if not soup:
            return []

        articles = []

        # Extract hero article
        hero_article = self.extract_hero_article(soup)
        if hero_article:
            articles.append(hero_article)

        # Extract sidebar articles
        sidebar_articles = self.extract_sidebar_articles(soup)
        articles.extend(sidebar_articles)

        # Extract below articles
        below_articles = self.extract_below_articles(soup)
        articles.extend(below_articles)

        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)

        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: x['date'], reverse=True)

        # Limit to 15 articles
        final_articles = unique_articles[:15]

        logger.info(f"Successfully scraped {len(final_articles)} unique articles")
        return final_articles

    def generate_rss(self, articles: List[Dict], output_file: str = "mls_next_news.xml") -> bool:
        """Generate RSS feed from scraped articles."""
        try:
            fg = FeedGenerator()
            fg.title('MLS NEXT News')
            fg.description('Latest news from MLS NEXT - the top youth soccer development program')
            fg.link(href=self.news_url)
            fg.language('en')
            fg.lastBuildDate(datetime.now(timezone.utc))

            for article in articles:
                fe = fg.add_entry()
                fe.title(article['title'])
                fe.link(href=article['link'])
                fe.description(article['description'])
                fe.published(article['date'])

                # Add image if available
                if article['image_url']:
                    fe.content(f'<img src="{article["image_url"]}" alt="{article["title"]}" />', type='html')

            # Write RSS feed to file
            fg.rss_file(output_file)
            logger.info(f"RSS feed generated successfully: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error generating RSS feed: {e}")
            return False

    def save_articles_json(self, articles: List[Dict], output_file: str = "mls_next_articles.json") -> bool:
        """Save articles to JSON file for debugging/backup."""
        try:
            # Convert datetime objects to ISO format for JSON serialization
            articles_for_json = []
            for article in articles:
                article_copy = article.copy()
                article_copy['date'] = article_copy['date'].isoformat()
                articles_for_json.append(article_copy)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles_for_json, f, indent=2, ensure_ascii=False)

            logger.info(f"Articles saved to JSON: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving articles to JSON: {e}")
            return False

def main():
    """Main function to run the scraper."""
    scraper = MLSNextScraper()

    logger.info("Starting MLS NEXT news scraping...")

    # Scrape articles
    articles = scraper.scrape_articles()

    if not articles:
        logger.error("No articles were scraped. Exiting.")
        return False

    # Generate RSS feed
    rss_success = scraper.generate_rss(articles)

    # Save articles to JSON for debugging
    json_success = scraper.save_articles_json(articles)

    if rss_success:
        logger.info("Scraping completed successfully!")
        return True
    else:
        logger.error("Failed to generate RSS feed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
