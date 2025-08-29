#!/usr/bin/env python3
"""
Content change detection script for MLS NEXT RSS scraper.
Compares RSS content to determine if deployment is needed.
Only considers title and link changes (description changes are ignored).
Now includes URL normalization to detect when MLS changes URL paths but articles are the same.
"""

import xml.etree.ElementTree as ET
import hashlib
import json
import os
import sys
import re
from urllib.parse import urlparse, parse_qs

# Configuration
ENABLE_URL_NORMALIZATION = True  # Set to False to disable URL normalization
MLS_DOMAINS = ['mlssoccer.com', 'www.mlssoccer.com']  # MLS domains to normalize


def normalize_mls_url(url: str) -> str:
    """
    Normalize MLS URLs to detect when articles are the same despite URL path changes.

    MLS often changes URL structures (e.g., /allstar/2025/news/ -> /mlsnext/news/)
    but the articles are the same content. This function extracts the key identifying
    information to help detect these cases.

    If URL normalization is disabled, returns the original URL unchanged.
    """
    if not ENABLE_URL_NORMALIZATION:
        return url

    if not url or not any(domain in url for domain in MLS_DOMAINS):
        return url

    try:
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Extract the article slug (the last part after the last slash)
        path_parts = [p for p in path.split('/') if p]

        # Handle different MLS URL patterns
        if len(path_parts) >= 2:
            # Check if this is a news listing page (ends with /news/)
            if path_parts[-1] == 'news' and len(path_parts) >= 2:
                # This is a news listing page, not an article
                return url

            # Look for the article slug (usually the last meaningful part)
            article_slug = None

            # Handle various MLS URL patterns
            if len(path_parts) >= 3 and path_parts[-2] == 'news':
                # Pattern: /category/news/article-slug
                article_slug = path_parts[-1]
            elif len(path_parts) >= 4 and path_parts[-3] == 'news':
                # Pattern: /category/year/news/article-slug
                article_slug = path_parts[-1]
            else:
                # Fallback: look for the last meaningful part
                for part in reversed(path_parts):
                    if part and part != 'news' and not part.isdigit() and len(part) > 3:
                        article_slug = part
                        break

            if article_slug:
                # Create a normalized version that focuses on the article identifier
                # rather than the category path
                return f"mlssoccer.com/article/{article_slug}"

        return url
    except Exception:
        return url


def extract_article_data(rss_file_path):
    """Extract article data from RSS file, excluding timestamps and metadata."""
    try:
        tree = ET.parse(rss_file_path)
        root = tree.getroot()

        articles = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            articles.append({'title': title, 'link': link, 'description': description})

        # Sort by title for consistent ordering
        articles.sort(key=lambda x: x['title'])

        return articles
    except Exception as e:
        print(f"Error parsing RSS file {rss_file_path}: {e}")
        return None


def create_content_hash(articles):
    """Create a hash based on article content (title and normalized link only)."""
    if not articles:
        return None

    # Include title and normalized link for change detection
    content_for_hash = []
    for article in articles:
        normalized_link = normalize_mls_url(article['link'])
        content_for_hash.append({
            'title': article['title'],
            'link': normalized_link
        })

    content_str = json.dumps(content_for_hash, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def compare_articles(prev_articles, new_articles):
    """Compare articles and return detailed change information."""
    if not prev_articles or not new_articles:
        return {
            'changed': True,
            'reason': 'Missing article data for comparison',
            'details': {}
        }

    changes = {
        'changed': False,
        'reason': 'No changes detected',
        'details': {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': [],
            'url_normalized': []  # Track URL normalization cases
        }
    }

    # Create lookup dictionaries using normalized URLs
    prev_lookup = {}
    new_lookup = {}

    for article in prev_articles:
        normalized_link = normalize_mls_url(article['link'])
        prev_lookup[article['title']] = {
            **article,
            'normalized_link': normalized_link
        }

    for article in new_articles:
        normalized_link = normalize_mls_url(article['link'])
        new_lookup[article['title']] = {
            **article,
            'normalized_link': normalized_link
        }

    # Find added articles
    for title in new_lookup:
        if title not in prev_lookup:
            changes['details']['added'].append({
                'title': title,
                'link': new_lookup[title]['link']
            })

    # Find removed articles
    for title in prev_lookup:
        if title not in new_lookup:
            changes['details']['removed'].append({
                'title': title,
                'link': prev_lookup[title]['link']
            })

    # Find modified articles - check title and normalized link changes
    for title in new_lookup:
        if title in prev_lookup:
            prev_article = prev_lookup[title]
            new_article = new_lookup[title]

            # Check if this is a URL normalization case
            if (prev_article['normalized_link'] == new_article['normalized_link'] and
                prev_article['link'] != new_article['link']):
                # Same article, different URL path - this is a URL normalization case
                changes['details']['url_normalized'].append({
                    'title': title,
                    'prev_link': prev_article['link'],
                    'new_link': new_article['link'],
                    'normalized_link': new_article['normalized_link']
                })
                # Don't count this as a modification
                changes['details']['unchanged'].append(title)
                continue

            # Check for actual modifications
            if (prev_article['title'] != new_article['title'] or
                prev_article['normalized_link'] != new_article['normalized_link']):
                changes['details']['modified'].append({
                    'title': title,
                    'prev_title': prev_article['title'],
                    'new_title': new_article['title'],
                    'prev_link': prev_article['link'],
                    'new_link': new_article['link'],
                    'prev_normalized': prev_article['normalized_link'],
                    'new_normalized': new_article['normalized_link']
                })
            else:
                changes['details']['unchanged'].append(title)

    # Determine if there are actual changes (excluding URL normalization)
    has_changes = (len(changes['details']['added']) > 0 or
                   len(changes['details']['removed']) > 0 or
                   len(changes['details']['modified']) > 0)

    changes['changed'] = has_changes

    if has_changes:
        change_reasons = []
        if changes['details']['added']:
            change_reasons.append(f"{len(changes['details']['added'])} new article(s)")
        if changes['details']['removed']:
            change_reasons.append(f"{len(changes['details']['removed'])} removed article(s)")
        if changes['details']['modified']:
            change_reasons.append(f"{len(changes['details']['modified'])} modified article(s)")

        changes['reason'] = f"Content changed: {', '.join(change_reasons)}"
    elif changes['details']['url_normalized']:
        changes['reason'] = f"No content changes detected (URLs normalized: {len(changes['details']['url_normalized'])} article(s))"

    return changes


def main():
    """Main function to check if content has changed."""
    if len(sys.argv) < 2:
        print("Usage: python check_content_changes.py <new_rss_file> [previous_rss_file]")
        print()
        print("Examples:")
        print("  python check_content_changes.py output/mls_next_news.xml")
        print("  python check_content_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml")
        print()
        print("This script only detects changes in article titles and normalized links.")
        print("Description changes are ignored since they're not visible to RSS readers.")
        print("URL path changes (when articles are the same) are also ignored.")
        print()
        print(f"URL Normalization: {'ENABLED' if ENABLE_URL_NORMALIZATION else 'DISABLED'}")
        sys.exit(1)

    # Check for help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        print("MLS NEXT RSS Change Detection Script")
        print("====================================")
        print()
        print("Usage: python check_content_changes.py <new_rss_file> [previous_rss_file]")
        print()
        print("This script compares RSS files and detects meaningful changes:")
        print("✅ New articles added")
        print("✅ Articles removed")
        print("✅ Article titles changed")
        print("✅ Article content changed (different normalized URLs)")
        print("❌ Description changes (ignored)")
        print("❌ Metadata changes (ignored)")
        print("❌ URL path changes when articles are the same (ignored)")
        print()
        print(f"URL Normalization: {'ENABLED' if ENABLE_URL_NORMALIZATION else 'DISABLED'}")
        if ENABLE_URL_NORMALIZATION:
            print("   This helps prevent false positives when MLS changes URL paths.")
        else:
            print("   URL normalization is disabled - all URL changes will be treated as modifications.")
        print()
        print("Examples:")
        print("  python check_content_changes.py output/mls_next_news.xml")
        print("  python check_content_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml")
        sys.exit(0)

    new_rss_file = sys.argv[1]
    prev_rss_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Extract article data from new RSS file
    new_articles = extract_article_data(new_rss_file)
    if new_articles is None:
        print("changed=true")
        print("reason=Error: Could not parse new RSS file")
        sys.exit(1)

    new_hash = create_content_hash(new_articles)
    print(f"new_hash={new_hash}")

    # Check if we have a previous file to compare against
    if prev_rss_file and os.path.exists(prev_rss_file):
        try:
            prev_articles = extract_article_data(prev_rss_file)
            if prev_articles is not None:
                prev_hash = create_content_hash(prev_articles)
                print(f"prev_hash={prev_hash}")

                if new_hash != prev_hash:
                    # Detailed comparison
                    changes = compare_articles(prev_articles, new_articles)

                    print(f"changed={str(changes['changed']).lower()}")
                    print(f"reason={changes['reason']}")

                    # Output detailed changes for GitHub Actions
                    print(f"added_count={len(changes['details']['added'])}")
                    print(f"removed_count={len(changes['details']['removed'])}")
                    print(f"modified_count={len(changes['details']['modified'])}")
                    print(f"url_normalized_count={len(changes['details']['url_normalized'])}")

                    # Log detailed article changes
                    if changes['details']['added']:
                        print("=== NEW ARTICLES ===")
                        for article in changes['details']['added']:
                            print(f"➕ {article['title']}")
                            print(f"   Link: {article['link']}")
                            print()

                    if changes['details']['removed']:
                        print("=== REMOVED ARTICLES ===")
                        for article in changes['details']['removed']:
                            print(f"➖ {article['title']}")
                            print(f"   Link: {article['link']}")
                            print()

                    if changes['details']['modified']:
                        print("=== MODIFIED ARTICLES ===")
                        for article in changes['details']['modified']:
                            print(f"🔄 {article['title']}")
                            if article['prev_title'] != article['new_title']:
                                print(f"   Title: {article['prev_title']} → {article['new_title']}")
                            if article['prev_normalized'] != article['new_normalized']:
                                print(f"   Normalized Link: {article['prev_normalized']} → {article['new_normalized']}")
                            if article['prev_link'] != article['new_link']:
                                print(f"   Link: {article['prev_link']} → {article['new_link']}")
                            print()

                    if changes['details']['url_normalized']:
                        print("=== URL NORMALIZED ARTICLES ===")
                        for article in changes['details']['url_normalized']:
                            print(f"🔗 {article['title']}")
                            print(f"   Link: {article['prev_link']} → {article['new_link']}")
                            print(f"   Normalized: {article['normalized_link']}")
                            print()

                else:
                    print("changed=false")
                    print("reason=No content changes detected")
            else:
                print("changed=true")
                print("reason=Error: Could not parse previous RSS file")
        except Exception as e:
            print("changed=true")
            print(f"reason=Error comparing with previous: {e}")
    else:
        print("changed=true")
        print("reason=Previous file not found, deploying")


if __name__ == "__main__":
    main()
