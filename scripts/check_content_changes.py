#!/usr/bin/env python3
"""
Content change detection script for MLS NEXT RSS scraper.
Compares RSS content to determine if deployment is needed.
"""

import xml.etree.ElementTree as ET
import hashlib
import json
import os
import sys


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
    """Create a hash based on article content."""
    if not articles:
        return None

    content_str = json.dumps(articles, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def main():
    """Main function to check if content has changed."""
    if len(sys.argv) < 2:
        print("Usage: python check_content_changes.py <new_rss_file> [previous_rss_file]")
        sys.exit(1)

    new_rss_file = sys.argv[1]
    prev_rss_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Extract article data from new RSS file
    new_articles = extract_article_data(new_rss_file)
    if new_articles is None:
        print("changed=true")
        print("Error: Could not parse new RSS file")
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
                    print("changed=true")
                    print(f"Content changed: {prev_hash} -> {new_hash}")
                else:
                    print("changed=false")
                    print("No content changes detected")
            else:
                print("changed=true")
                print("Error: Could not parse previous RSS file")
        except Exception as e:
            print("changed=true")
            print(f"Error comparing with previous: {e}")
    else:
        print("changed=true")
        print("Previous file not found, deploying")


if __name__ == "__main__":
    main()
