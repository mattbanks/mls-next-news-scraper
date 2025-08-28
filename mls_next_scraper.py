#!/usr/bin/env python3
"""
MLS NEXT News Scraper
Scrapes news articles from https://www.mlssoccer.com/mlsnext/news/
and generates an RSS feed.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, TypedDict
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import pytz
from dateutil import parser
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Article(TypedDict):
    """Type definition for article data structure."""
    title: str
    link: str
    description: str
    image_url: str
    date: datetime
    is_hero: bool

class MLSNextScraper:
    """Scraper for MLS NEXT news articles."""

    @staticmethod
    def _escape_xml_text(text: str) -> str:
        """Escape special characters for XML output."""
        if not text:
            return ""
        # Escape XML special characters with proper XML entities
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text

    @staticmethod
    def _escape_json_text(text: str) -> str:
        """Escape special characters for JSON output."""
        if not text:
            return ""
        # JSON only needs to escape quotes and backslashes
        # Apostrophes and other characters are fine in JSON
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        return text

    def __init__(self):
        self.base_url = "https://www.mlssoccer.com"
        self.news_url = f"{self.base_url}/mlsnext/news/"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session.headers.update(self.headers)

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

    def extract_hero_article(self, soup: BeautifulSoup) -> Optional[Article]:
        """Extract the main hero article."""
        try:
            # Look for the hero article - it's the first large article at the top
            hero_selectors = [
                'article.fm-card.-default',  # First large article
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
                # Fallback: look for the first article with fm-card class
                hero_article = soup.find('article', class_=re.compile(r'fm-card'))

            if hero_article:
                return self._extract_article_data(hero_article, is_hero=True)

            return None

        except Exception as e:
            logger.error(f"Error extracting hero article: {e}")
            return None

    def extract_sidebar_articles(self, soup: BeautifulSoup) -> List[Article]:
        """Extract the horizontal articles (second row)."""
        articles = []
        try:
            # Look for horizontal articles - they're the second row of articles
            horizontal_selectors = [
                'article.fm-card.-horizontal',  # Horizontal layout articles
                'div[class*="horizontal"] article',
                'div[class*="secondary"] article'
            ]

            for selector in horizontal_selectors:
                horizontal_articles = soup.select(selector)
                if horizontal_articles:
                    for article in horizontal_articles[:5]:  # Limit to 5
                        article_data = self._extract_article_data(article)
                        if article_data:
                            articles.append(article_data)
                    break

            # If no horizontal articles found, try alternative approach
            if not articles:
                # Look for all fm-card articles and skip the first (hero)
                all_articles = soup.find_all('article', class_=re.compile(r'fm-card'))
                if len(all_articles) > 1:
                    # Skip the first one (hero) and take the next 5
                    for article in all_articles[1:6]:
                        article_data = self._extract_article_data(article)
                        if article_data:
                            articles.append(article_data)

            logger.info(f"Extracted {len(articles)} horizontal articles")
            return articles

        except Exception as e:
            logger.error(f"Error extracting horizontal articles: {e}")
            return []

    def extract_below_articles(self, soup: BeautifulSoup) -> List[Article]:
        """Extract remaining articles beyond the first 6."""
        articles = []
        try:
            # Get all fm-card articles and take the remaining ones
            all_articles = soup.find_all('article', class_=re.compile(r'fm-card'))

            if len(all_articles) > 6:
                # Skip the first 6 articles (hero + 5 horizontal) and take the next 10
                remaining_articles = all_articles[6:16]
                for article in remaining_articles:
                    article_data = self._extract_article_data(article)
                    if article_data:
                        articles.append(article_data)

            logger.info(f"Extracted {len(articles)} remaining articles")
            return articles

        except Exception as e:
            logger.error(f"Error extracting remaining articles: {e}")
            return []

    def _extract_article_data(self, article_element: BeautifulSoup, is_hero: bool = False) -> Optional[Article]:
        """Extract article data from a BeautifulSoup article element."""
        try:
            # Extract title - look for fa-text__title class first
            title_elem = article_element.find(['h1', 'h2', 'h3', 'h4'], class_='fa-text__title')
            if not title_elem:
                # Fallback to any heading
                title_elem = article_element.find(['h1', 'h2', 'h3', 'h4'])

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # Extract link - look for parent anchor tag
            link_elem = article_element.find_parent('a')
            if not link_elem or not link_elem.get('href'):
                # Fallback to any anchor in the article
                link_elem = article_element.find('a')

            if not link_elem or not link_elem.get('href'):
                return None

            link = link_elem['href']
            if not link.startswith('http'):
                link = self.base_url + link

            # Extract description and date from the actual article page
            description, article_date = self._fetch_article_details(link)

            # Extract image - look for data-src first (lazy loading)
            image_url = ""
            img_elem = article_element.find('img')
            if img_elem:
                image_url = img_elem.get('data-src') or img_elem.get('src')
                if image_url and not image_url.startswith('http'):
                    image_url = self.base_url + image_url

            # Use article date if found, otherwise current time
            if not article_date:
                article_date = datetime.now(timezone.utc)

            return {
                'title': title,
                'link': link,
                'description': description,
                'image_url': image_url,
                'date': article_date,
                'is_hero': is_hero
            }

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None

    def _fetch_article_details(self, article_url: str) -> Tuple[str, Optional[datetime]]:
        """Fetch article description and date from the individual article page."""
        try:
            response = requests.get(article_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract description from meta tags
            description = ""
            desc_meta = soup.find('meta', {'name': 'description'})
            if desc_meta and desc_meta.get('content'):
                description = desc_meta['content'].strip()

            # Extract date from data-datetime attribute
            article_date = None
            date_elem = soup.find('p', {'js-date-time-to-convert': ''})
            if date_elem and date_elem.get('data-datetime'):
                try:
                    date_text = date_elem['data-datetime']
                    article_date = parser.parse(date_text)
                    if article_date.tzinfo is None:
                        article_date = pytz.UTC.localize(article_date)
                except Exception as e:
                    logger.warning(f"Could not parse date '{date_text}': {e}")

            return description, article_date

        except Exception as e:
            logger.warning(f"Could not fetch article details for {article_url}: {e}")
            return "", None

    def scrape_articles(self) -> List[Article]:
        """Main method to scrape all articles."""
        soup = self.fetch_page()
        if not soup:
            return []

        articles = []

        # Extract hero article
        hero_article = self.extract_hero_article(soup)
        if hero_article:
            articles.append(hero_article)

        # Extract horizontal articles
        horizontal_articles = self.extract_sidebar_articles(soup)
        articles.extend(horizontal_articles)

        # Extract remaining articles
        remaining_articles = self.extract_below_articles(soup)
        articles.extend(remaining_articles)

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

    def generate_rss(self, articles: List[Article], output_file: str = "mls_next_news.xml") -> bool:
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
                fe.title(self._escape_xml_text(article['title']))
                fe.link(href=article['link'])
                fe.description(self._escape_xml_text(article['description']))
                fe.published(article['date'])

                # Add image if available
                if article['image_url']:
                    escaped_title = self._escape_xml_text(article['title'])
                    fe.content(f'<img src="{article["image_url"]}" alt="{escaped_title}" />', type='html')

            # Write RSS feed to file
            fg.rss_file(output_file)
            logger.info(f"RSS feed generated successfully: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error generating RSS feed: {e}")
            return False

    def save_articles_json(self, articles: List[Article], output_file: str = "mls_next_articles.json") -> bool:
        """Save articles to JSON file for debugging/backup."""
        try:
            # Convert datetime objects to ISO format for JSON serialization
            articles_for_json = []
            for article in articles:
                article_copy = article.copy()
                article_copy['date'] = article_copy['date'].isoformat()

                # Escape text fields for JSON
                article_copy['title'] = self._escape_json_text(article_copy['title'])
                article_copy['description'] = self._escape_json_text(article_copy['description'])

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
    from config import RSS_OUTPUT_FILE, JSON_OUTPUT_FILE

    scraper = MLSNextScraper()

    logger.info("Starting MLS NEXT news scraping...")

    # Scrape articles
    articles = scraper.scrape_articles()

    if not articles:
        logger.error("No articles were scraped. Exiting.")
        return False

    # Generate RSS feed
    rss_success = scraper.generate_rss(articles, str(RSS_OUTPUT_FILE))

    # Save articles to JSON for debugging
    json_success = scraper.save_articles_json(articles, str(JSON_OUTPUT_FILE))

    if rss_success:
        logger.info("Scraping completed successfully!")
        return True
    else:
        logger.error("Failed to generate RSS feed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
