#!/usr/bin/env python3
"""
Test script for the updated change detection functionality.
Tests that URL normalization correctly prevents false positives when MLS changes URL paths.
"""

import sys
import os
import tempfile
import json

# Add the parent directory to the path so we can import the function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.check_content_changes import extract_article_data, create_content_hash, compare_articles


def create_test_rss_file(articles, filename):
    """Create a test RSS file with the given articles."""
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>MLS NEXT News</title>
    <link>https://www.mlssoccer.com/mlsnext/news/</link>
    <description>MLS NEXT News Feed</description>
"""

    for article in articles:
        rss_content += f"""
    <item>
        <title>{article['title']}</title>
        <link>{article['link']}</link>
        <description>{article['description']}</description>
    </item>"""

    rss_content += """
</channel>
</rss>"""

    with open(filename, 'w') as f:
        f.write(rss_content)


def test_url_normalization_scenario():
    """Test the scenario from the logs where MLS changed URL paths."""

    print("Testing URL normalization scenario from logs...")
    print("=" * 70)

    # Create test data based on the logs
    prev_articles = [
        {
            'title': '2025 MLS NEXT All-Star Game: East snatches late win over West',
            'link': 'https://www.mlssoccer.com/allstar/2025/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west',
            'description': 'Test description'
        },
        {
            'title': 'Generation adidas Cup: MLS champions guaranteed after U16 & U18 semifinals',
            'link': 'https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals',
            'description': 'Test description'
        }
    ]

    new_articles = [
        {
            'title': '2025 MLS NEXT All-Star Game: East snatches late win over West',
            'link': 'https://www.mlssoccer.com/mlsnext/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west',
            'description': 'Test description'
        },
        {
            'title': 'Generation adidas Cup: MLS champions guaranteed after U16 & U18 semifinals',
            'link': 'https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals',
            'description': 'Test description'
        }
    ]

    print("Previous articles:")
    for article in prev_articles:
        print(f"  - {article['title']}")
        print(f"    Link: {article['link']}")

    print("\nNew articles:")
    for article in new_articles:
        print(f"  - {article['title']}")
        print(f"    Link: {article['link']}")

    # Test the comparison
    print("\n" + "=" * 70)
    print("Running comparison...")

    changes = compare_articles(prev_articles, new_articles)

    print(f"Changed: {changes['changed']}")
    print(f"Reason: {changes['reason']}")
    print(f"Added: {len(changes['details']['added'])}")
    print(f"Removed: {len(changes['details']['removed'])}")
    print(f"Modified: {len(changes['details']['modified'])}")
    print(f"URL Normalized: {len(changes['details']['url_normalized'])}")
    print(f"Unchanged: {len(changes['details']['unchanged'])}")

    if changes['details']['url_normalized']:
        print("\nURL Normalized Articles:")
        for article in changes['details']['url_normalized']:
            print(f"  🔗 {article['title']}")
            print(f"     Previous: {article['prev_link']}")
            print(f"     New: {article['new_link']}")
            print(f"     Normalized: {article['normalized_link']}")

    # Test the hash creation
    print("\n" + "=" * 70)
    print("Testing hash creation...")

    prev_hash = create_content_hash(prev_articles)
    new_hash = create_content_hash(new_articles)

    print(f"Previous hash: {prev_hash}")
    print(f"New hash: {new_hash}")
    print(f"Hashes match: {prev_hash == new_hash}")

    # The hashes should match because the normalized URLs are the same
    if prev_hash == new_hash:
        print("✅ SUCCESS: URLs are correctly normalized - no false positive!")
    else:
        print("❌ FAILURE: URLs are not being normalized correctly")

    return changes['changed'] == False


def test_actual_content_change():
    """Test that actual content changes are still detected."""

    print("\n\nTesting actual content change detection...")
    print("=" * 70)

    prev_articles = [
        {
            'title': 'Article 1',
            'link': 'https://www.mlssoccer.com/mlsnext/news/article-1',
            'description': 'Test description'
        }
    ]

    new_articles = [
        {
            'title': 'Article 1 Updated',  # Title changed
            'link': 'https://www.mlssoccer.com/mlsnext/news/article-1',
            'description': 'Test description'
        }
    ]

    print("Previous articles:")
    for article in prev_articles:
        print(f"  - {article['title']}")

    print("\nNew articles:")
    for article in new_articles:
        print(f"  - {article['title']}")

    changes = compare_articles(prev_articles, new_articles)

    print(f"\nChanged: {changes['changed']}")
    print(f"Reason: {changes['reason']}")

    if changes['changed']:
        print("✅ SUCCESS: Actual content changes are still detected!")
    else:
        print("❌ FAILURE: Content changes are not being detected!")

    return changes['changed'] == True


if __name__ == "__main__":
    print("MLS Change Detection Test Suite")
    print("=" * 70)

    # Test URL normalization scenario
    url_test_passed = test_url_normalization_scenario()

    # Test actual content change detection
    content_test_passed = test_actual_content_change()

    print("\n" + "=" * 70)
    print("Test Results:")
    print(f"URL Normalization Test: {'✅ PASSED' if url_test_passed else '❌ FAILED'}")
    print(f"Content Change Test: {'✅ PASSED' if content_test_passed else '❌ FAILED'}")

    if url_test_passed and content_test_passed:
        print("\n🎉 All tests passed! The URL normalization is working correctly.")
    else:
        print("\n💥 Some tests failed. Please review the implementation.")
