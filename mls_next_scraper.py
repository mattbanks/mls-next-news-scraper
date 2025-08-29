#!/usr/bin/env python3
"""
MLS NEXT News Scraper
Scrapes news articles from https://www.mlssoccer.com/mlsnext/news/
and generates an RSS feed.
"""

import requests
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, TypedDict
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import pytz
from dateutil import parser
import json
import re
import hashlib

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

    @staticmethod
    def _clean_text_for_rss(text: str) -> str:
        """Clean and normalize text for RSS feeds."""
        if not text:
            return ""

        # Normalize whitespace - replace multiple spaces and newlines with single spaces
        import re
        text = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove any remaining problematic characters
        text = text.replace('\r', ' ').replace('\n', ' ')

        # Don't manually escape XML - feedgen handles this automatically
        return text

    def __init__(self):
        from config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, RETRY_DELAY, USER_AGENT

        self.base_url = "https://www.mlssoccer.com"
        self.news_url = f"{self.base_url}/mlsnext/news/"
        self.session = requests.Session()
        self.headers = {'User-Agent': USER_AGENT}
        self.session.headers.update(self.headers)

        # Rate limiting and retry settings
        self.request_timeout = REQUEST_TIMEOUT
        self.request_delay = REQUEST_DELAY
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.last_request_time = 0

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request_with_retry(self, url: str, timeout: Optional[int] = None) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting."""
        if timeout is None:
            timeout = self.request_timeout

        for attempt in range(self.max_retries + 1):
            try:
                self._rate_limit()
                logger.debug(f"Making request to {url} (attempt {attempt + 1}/{self.max_retries + 1})")

                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed to fetch {url} after {self.max_retries + 1} attempts: {e}")
                    return None
                else:
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

        return None

    def fetch_page(self) -> Optional[BeautifulSoup]:
        """Fetch the news page and return BeautifulSoup object."""
        try:
            logger.info(f"Fetching page: {self.news_url}")
            response = self._make_request_with_retry(self.news_url)

            if not response:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info("Page fetched successfully")
            return soup

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
            for i, selector in enumerate(hero_selectors):
                hero_article = soup.select_one(selector)
                if hero_article:
                    logger.debug(f"Found hero article with selector {i+1}: {selector}")
                    break

            if not hero_article:
                # Fallback: look for the first article with fm-card class
                hero_article = soup.find('article', class_=re.compile(r'fm-card'))
                if hero_article:
                    logger.debug("Found hero article using fallback fm-card selector")
                else:
                    logger.warning("No hero article found with any selector")

            if hero_article:
                article_data = self._extract_article_data(hero_article, is_hero=True)
                if article_data:
                    logger.info(f"Successfully extracted hero article: {article_data['title']}")
                    return article_data
                else:
                    logger.warning("Hero article found but data extraction failed")

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
            logger.debug(f"Extracting {'hero' if is_hero else 'regular'} article data")

            # Extract title - look for fa-text__title class first
            title_elem = article_element.find(['h1', 'h2', 'h3', 'h4'], class_='fa-text__title')
            if not title_elem:
                # Fallback to any heading
                title_elem = article_element.find(['h1', 'h2', 'h3', 'h4'])
                logger.debug("Used fallback title selector")

            if not title_elem:
                logger.warning("No title element found in article")
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                logger.warning("Empty title found in article")
                return None

            logger.debug(f"Found title: {title}")

            # Extract link - look for parent anchor tag
            link_elem = article_element.find_parent('a')
            if not link_elem or not link_elem.get('href'):
                # Fallback to any anchor in the article
                link_elem = article_element.find('a')
                logger.debug("Used fallback link selector")

            if not link_elem or not link_elem.get('href'):
                logger.warning(f"No link found for article: {title}")
                return None

            link = link_elem['href']
            if not link.startswith('http'):
                link = self.base_url + link

            logger.debug(f"Found link: {link}")

            # Extract description and date from the actual article page
            description, article_date = self._fetch_article_details(link)

            # Extract image - look for data-src first (lazy loading)
            image_url = ""
            img_elem = article_element.find('img')
            if img_elem:
                image_url = img_elem.get('data-src') or img_elem.get('src')
                if image_url and not image_url.startswith('http'):
                    image_url = self.base_url + image_url
                logger.debug(f"Found image: {image_url}")
            else:
                logger.debug("No image found for article")

            # Use article date if found, otherwise current time
            if not article_date:
                article_date = datetime.now(timezone.utc)
                logger.debug("Using current time as fallback date")

            article_data = {
                'title': title,
                'link': link,
                'description': description,
                'image_url': image_url,
                'date': article_date,
                'is_hero': is_hero
            }

            logger.debug(f"Successfully extracted article: {title[:50]}...")
            return article_data

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None

    def _fetch_article_details(self, article_url: str) -> Tuple[str, Optional[datetime]]:
        """Fetch article description and date from the individual article page."""
        try:
            logger.debug(f"Fetching details for article: {article_url}")
            response = self._make_request_with_retry(article_url)

            if not response:
                logger.warning(f"Failed to fetch article details for {article_url}")
                return "", None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract description from meta tags
            description = ""
            desc_meta = soup.find('meta', {'name': 'description'})
            if desc_meta and desc_meta.get('content'):
                description = desc_meta['content'].strip()
                logger.debug(f"Found description: {description[:50]}...")
            else:
                logger.debug(f"No description meta tag found for {article_url}")

            # Extract date from data-datetime attribute
            article_date = None
            date_elem = soup.find('p', {'js-date-time-to-convert': ''})
            if date_elem and date_elem.get('data-datetime'):
                try:
                    date_text = date_elem['data-datetime']
                    article_date = parser.parse(date_text)
                    if article_date.tzinfo is None:
                        article_date = pytz.UTC.localize(article_date)
                    logger.debug(f"Found date: {article_date}")
                except Exception as e:
                    logger.warning(f"Could not parse date '{date_text}' for {article_url}: {e}")
            else:
                logger.debug(f"No date element found for {article_url}")

            return description, article_date

        except Exception as e:
            logger.error(f"Unexpected error fetching article details for {article_url}: {e}")
            return "", None

    def scrape_articles(self) -> List[Article]:
        """Main method to scrape all articles."""
        soup = self.fetch_page()
        if not soup:
            return []

        articles = []
        logger.info("Starting article extraction process...")

        # Extract hero article
        hero_article = self.extract_hero_article(soup)
        if hero_article:
            articles.append(hero_article)
            logger.info(f"✅ Hero article extracted: {hero_article['title'][:50]}...")
        else:
            logger.warning("❌ No hero article found")

        # Extract horizontal articles
        horizontal_articles = self.extract_sidebar_articles(soup)
        articles.extend(horizontal_articles)
        logger.info(f"✅ Horizontal articles extracted: {len(horizontal_articles)} articles")

        # Extract remaining articles
        remaining_articles = self.extract_below_articles(soup)
        articles.extend(remaining_articles)
        logger.info(f"✅ Remaining articles extracted: {len(remaining_articles)} articles")

        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        duplicate_count = 0

        for article in articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
            else:
                duplicate_count += 1
                logger.debug(f"Duplicate article found: {article['title'][:50]}...")

        if duplicate_count > 0:
            logger.info(f"🔄 Removed {duplicate_count} duplicate articles")

        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: x['date'], reverse=True)

        # Limit to 15 articles
        final_articles = unique_articles[:15]
        if len(unique_articles) > 15:
            logger.info(f"📊 Limited to 15 articles (had {len(unique_articles)} total)")

        # Log summary of final articles
        logger.info("📰 Final article summary:")
        for i, article in enumerate(final_articles):
            date_str = article['date'].strftime('%Y-%m-%d %H:%M')
            hero_indicator = "⭐ " if article['is_hero'] else "  "
            logger.info(f"   {i+1:2d}. {hero_indicator}{article['title'][:60]}{'...' if len(article['title']) > 60 else ''}")
            logger.info(f"       📅 {date_str} | 🔗 {article['link']}")

        logger.info(f"✅ Successfully scraped {len(final_articles)} unique articles")
        return final_articles

    def generate_rss(self, articles: List[Article], output_file: str = "mls_next_news.xml") -> bool:
        """Generate RSS feed from scraped articles."""
        try:
            fg = FeedGenerator()

            # Enhanced RSS channel metadata
            fg.title('MLS NEXT News')
            fg.description('Latest news from MLS NEXT - the top youth soccer development program')
            fg.link(href=self.news_url)
            fg.language('en')
            fg.lastBuildDate(datetime.now(timezone.utc))

            # Optional metadata - add what's compatible
            try:
                fg.copyright('© MLS. All rights reserved.')
            except Exception:
                pass

            try:
                fg.managingEditor('noreply@mlssoccer.com (MLS NEXT)')
            except Exception:
                pass

            try:
                fg.webMaster('noreply@mlssoccer.com (MLS NEXT)')
            except Exception:
                pass

            # Add RSS 2.0 image
            try:
                fg.image(url='https://www.mlssoccer.com/sites/default/files/mls_logo.png',
                        title='MLS NEXT News',
                        link=self.news_url,
                        description='MLS NEXT Logo')
            except Exception as e:
                logger.warning(f"Could not add RSS image: {e}")

            for article in articles:
                fe = fg.add_entry()

                # Clean and normalize text for RSS - feedgen handles XML escaping automatically
                clean_title = self._clean_text_for_rss(article['title'])
                clean_description = self._clean_text_for_rss(article['description'])

                fe.title(clean_title)
                fe.link(href=article['link'])
                fe.description(clean_description)
                fe.published(article['date'])

                # Generate unique GUID based on article URL
                article_guid = self._generate_guid(article['link'])
                fe.guid(article_guid, permalink=True)

                # Add categories for better organization (if supported)
                try:
                    fe.category('MLS NEXT')
                    if 'generation adidas cup' in clean_title.lower():
                        fe.category('Generation adidas Cup')
                    if 'all-star' in clean_title.lower():
                        fe.category('All-Star Game')
                    if 'cup' in clean_title.lower():
                        fe.category('Cup Competition')
                    if 'award' in clean_title.lower():
                        fe.category('Awards')
                    if 'recap' in clean_title.lower():
                        fe.category('Monthly Recap')
                except Exception:
                    # Categories not supported in this feedgen version
                    pass

                # Add image if available - create proper HTML content
                if article['image_url']:
                    # Create rich content with both image and description
                    html_content = f'<p>{clean_description}</p>'
                    if article['image_url']:
                        html_content = f'<img src="{article["image_url"]}" alt="{clean_title}" style="max-width: 100%; height: auto;" /><br/><br/>{html_content}'
                    fe.content(html_content, type='html')

            # Write RSS feed to file
            fg.rss_file(output_file)
            logger.info(f"RSS feed generated successfully: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error generating RSS feed: {e}")
            return False

    def _generate_guid(self, url: str) -> str:
        """Generate a unique GUID for an article based on its URL."""
        # Create a stable hash of the URL
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def save_articles_json(self, articles: List[Article], output_file: str = "mls_next_articles.json") -> bool:
        """Save articles to JSON file for debugging/backup."""
        try:
            # Convert datetime objects to ISO format for JSON serialization
            articles_for_json = []
            for article in articles:
                article_copy = article.copy()
                article_copy['date'] = article_copy['date'].isoformat()

                # Clean and normalize text fields for JSON (same as RSS)
                article_copy['title'] = self._clean_text_for_rss(article_copy['title'])
                article_copy['description'] = self._clean_text_for_rss(article_copy['description'])

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
