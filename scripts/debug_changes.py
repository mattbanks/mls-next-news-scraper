#!/usr/bin/env python3
"""
Debug script to analyze RSS content and identify what's causing change detection.
This helps troubleshoot false positive deployments.
Focuses on title and link changes only (description changes are ignored).
"""

import xml.etree.ElementTree as ET
import json
import os
import sys
from datetime import datetime
import hashlib

def analyze_rss_file(file_path, label="RSS"):
    """Analyze an RSS file and return detailed information."""
    if not os.path.exists(file_path):
        print(f"❌ {label} file not found: {file_path}")
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract metadata
        channel = root.find('channel')
        if channel is not None:
            title = channel.find('title').text if channel.find('title') is not None else 'N/A'
            last_build = channel.find('lastBuildDate').text if channel.find('lastBuildDate') is not None else 'N/A'
            pub_date = channel.find('pubDate').text if channel.find('pubDate') is not None else 'N/A'
        else:
            title = 'N/A'
            last_build = 'N/A'
            pub_date = 'N/A'

        # Extract articles
        articles = []
        for item in root.findall('.//item'):
            article = {
                'title': item.find('title').text if item.find('title') is not None else '',
                'link': item.find('link').text if item.find('link') is not None else '',
                'description': item.find('description').text if item.find('description') is not None else '',
                'pub_date': item.find('pubDate').text if item.find('pubDate') is not None else '',
                'guid': item.find('guid').text if item.find('guid') is not None else ''
            }
            articles.append(article)

        # Create content hash (title and link only, excluding descriptions and timestamps)
        content_for_hash = []
        for article in articles:
            content_for_hash.append({
                'title': article['title'],
                'link': article['link']
            })

        content_str = json.dumps(content_for_hash, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        return {
            'file_path': file_path,
            'metadata': {
                'title': title,
                'last_build': last_build,
                'pub_date': pub_date
            },
            'articles': articles,
            'content_hash': content_hash,
            'article_count': len(articles)
        }

    except Exception as e:
        print(f"❌ Error parsing {label} file: {e}")
        return None

def compare_rss_files(file1_path, file2_path, label1="Current", label2="Previous"):
    """Compare two RSS files and show differences."""
    print(f"🔍 Comparing RSS files:")
    print(f"   {label1}: {file1_path}")
    print(f"   {label2}: {file2_path}")
    print()

    # Analyze both files
    file1_data = analyze_rss_file(file1_path, label1)
    file2_data = analyze_rss_file(file2_path, label2)

    if not file1_data or not file2_data:
        return

    print(f"📊 File Analysis:")
    print(f"   {label1}: {file1_data['article_count']} articles, hash: {file1_data['content_hash'][:16]}...")
    print(f"   {label2}: {file2_data['article_count']} articles, hash: {file2_data['content_hash'][:16]}...")
    print()

    # Compare metadata
    print(f"📋 Metadata Comparison:")
    for key in ['title', 'last_build', 'pub_date']:
        val1 = file1_data['metadata'][key]
        val2 = file2_data['metadata'][key]
        if val1 != val2:
            print(f"   ❌ {key}:")
            print(f"      {label1}: {val1}")
            print(f"      {label2}: {val2}")
        else:
            print(f"   ✅ {key}: {val1}")
    print()

    # Compare content hashes
    if file1_data['content_hash'] == file2_data['content_hash']:
        print("✅ Content hashes match - no actual content changes")
    else:
        print("❌ Content hashes differ - content has changed")
        print()

        # Detailed article comparison
        print("📝 Article Comparison:")

        # Create lookup dictionaries
        articles1 = {article['title']: article for article in file1_data['articles']}
        articles2 = {article['title']: article for article in file2_data['articles']}

        # Find added articles
        added = [title for title in articles1 if title not in articles2]
        if added:
            print(f"   ➕ Added articles ({len(added)}):")
            for title in added[:5]:  # Show first 5
                article = articles1[title]
                print(f"      • {title}")
                print(f"        Link: {article['link']}")
                print(f"        Description: {article['description'][:80]}{'...' if len(article['description']) > 80 else ''}")
            if len(added) > 5:
                print(f"      ... and {len(added) - 5} more")

        # Find removed articles
        removed = [title for title in articles2 if title not in articles1]
        if removed:
            print(f"   ➖ Removed articles ({len(removed)}):")
            for title in removed[:5]:  # Show first 5
                article = articles2[title]
                print(f"      • {title}")
                print(f"        Link: {article['link']}")
                print(f"        Description: {article['description'][:80]}{'...' if len(article['description']) > 80 else ''}")
            if len(removed) > 5:
                print(f"      ... and {len(removed) - 5} more")

        # Find modified articles - ONLY check title and link changes
        modified = []
        for title in articles1:
            if title in articles2:
                article1 = articles1[title]
                article2 = articles2[title]
                if (article1['title'] != article2['title'] or
                    article1['link'] != article2['link']):
                    modified.append((title, article1, article2))

        if modified:
            print(f"   🔄 Modified articles ({len(modified)}):")
            for title, article1, article2 in modified[:3]:  # Show first 3
                print(f"      • {title}")
                if article1['title'] != article2['title']:
                    print(f"        Title: {article2['title']} → {article1['title']}")
                if article1['link'] != article2['link']:
                    print(f"        Link: {article2['link']} → {article1['link']}")
                print(f"        Description: {article2['description'][:80]}{'...' if len(article2['description']) > 80 else ''}")
                print(f"        → {article1['description'][:80]}{'...' if len(article1['description']) > 80 else ''}")

        # Show unchanged articles count
        unchanged = [title for title in articles1 if title in articles2 and
                    articles1[title]['title'] == articles2[title]['title'] and
                    articles1[title]['link'] == articles2[title]['link']]
        if unchanged:
            print(f"   ✅ Unchanged articles: {len(unchanged)}")

    print()
    print("=" * 80)

def main():
    """Main function to debug RSS changes."""
    if len(sys.argv) < 2:
        print("Usage: python debug_changes.py <current_rss_file> [previous_rss_file]")
        print()
        print("Examples:")
        print("  python debug_changes.py output/mls_next_news.xml")
        print("  python debug_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml")
        sys.exit(1)

    # Check for help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        print("MLS NEXT RSS Change Debug Tool")
        print("====================================")
        print()
        print("Usage: python debug_changes.py <current_rss_file> [previous_rss_file]")
        print()
        print("This tool analyzes RSS files and shows detailed change information:")
        print("✅ File metadata and article counts")
        print("✅ Content hash analysis")
        print("✅ Article-by-article comparison")
        print("✅ Focus on title and link changes only")
        print("❌ Description changes are ignored")
        print()
        print("Examples:")
        print("  python debug_changes.py output/mls_next_news.xml")
        print("  python debug_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml")
        sys.exit(0)

    current_file = sys.argv[1]
    previous_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("🔍 MLS NEXT RSS Change Debug Tool")
    print("Focus: Title and Link Changes Only (Descriptions Ignored)")
    print("=" * 80)
    print()

    # Analyze current file
    current_data = analyze_rss_file(current_file, "Current")
    if current_data:
        print(f"📁 Current RSS File Analysis:")
        print(f"   File: {current_data['file_path']}")
        print(f"   Articles: {current_data['article_count']}")
        print(f"   Content Hash: {current_data['content_hash']}")
        print(f"   Title: {current_data['metadata']['title']}")
        print(f"   Last Build: {current_data['metadata']['last_build']}")
        print(f"   Pub Date: {current_data['metadata']['pub_date']}")
        print()

        # Show first few articles
        print("📰 First 3 Articles:")
        for i, article in enumerate(current_data['articles'][:3]):
            print(f"   {i+1}. {article['title']}")
            print(f"      Link: {article['link']}")
            print(f"      Description: {article['description'][:100]}{'...' if len(article['description']) > 100 else ''}")
            print()

    # Compare with previous file if provided
    if previous_file:
        compare_rss_files(current_file, previous_file, "Current", "Previous")
    else:
        print("💡 Tip: Provide a previous RSS file to compare changes:")
        print("   python debug_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml")

if __name__ == "__main__":
    main()
