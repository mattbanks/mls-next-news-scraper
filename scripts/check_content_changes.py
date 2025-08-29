#!/usr/bin/env python3
"""
Content change detection script for MLS NEXT RSS scraper.
Compares RSS content to determine if deployment is needed.
Only considers title and link changes (description changes are ignored).
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
    """Create a hash based on article content (title and link only)."""
    if not articles:
        return None

    # Only include title and link for change detection (ignore descriptions)
    content_for_hash = []
    for article in articles:
        content_for_hash.append({
            'title': article['title'],
            'link': article['link']
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
            'unchanged': []
        }
    }

    # Create lookup dictionaries
    prev_lookup = {article['title']: article for article in prev_articles}
    new_lookup = {article['title']: article for article in new_articles}

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

    # Find modified articles - ONLY check title and link changes
    # Description changes are ignored since they're not visible to RSS readers
    for title in new_lookup:
        if title in prev_lookup:
            prev_article = prev_lookup[title]
            new_article = new_lookup[title]

            # Only consider title or link changes as modifications
            if (prev_article['title'] != new_article['title'] or
                prev_article['link'] != new_article['link']):
                changes['details']['modified'].append({
                    'title': title,
                    'prev_title': prev_article['title'],
                    'new_title': new_article['title'],
                    'prev_link': prev_article['link'],
                    'new_link': new_article['link']
                })
            else:
                changes['details']['unchanged'].append(title)

    # Determine if there are actual changes
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
        print("This script only detects changes in article titles and links.")
        print("Description changes are ignored since they're not visible to RSS readers.")
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
        print("✅ Article links changed")
        print("❌ Description changes (ignored)")
        print("❌ Metadata changes (ignored)")
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
                            if article['prev_link'] != article['new_link']:
                                print(f"   Link: {article['prev_link']} → {article['new_link']}")
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
