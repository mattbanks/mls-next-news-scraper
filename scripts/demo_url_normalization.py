#!/usr/bin/env python3
"""
Demonstration script showing how URL normalization prevents false positives.
This script recreates the scenario from the logs where MLS changed URL paths
but the articles were the same content.
"""

import sys
import os

# Add the parent directory to the path so we can import the function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.check_content_changes import normalize_mls_url, create_content_hash, compare_articles


def demo_url_normalization():
    """Demonstrate URL normalization with real data from the logs."""

    print("MLS URL Normalization Demo")
    print("=" * 60)
    print("This demo shows how URL normalization prevents false positives")
    print("when MLS changes URL paths but articles remain the same.\n")

    # Real data from the logs
    print("📊 REAL DATA FROM LOGS:")
    print("MLS changed URLs for these articles, but they're the same content:\n")

    url_pairs = [
        {
            'title': '2025 MLS NEXT All-Star Game: East snatches late win over West',
            'old_url': 'https://www.mlssoccer.com/allstar/2025/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west',
            'new_url': 'https://www.mlssoccer.com/mlsnext/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west'
        },
        {
            'title': 'Generation adidas Cup: MLS champions guaranteed after U16 & U18 semifinals',
            'old_url': 'https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals',
            'new_url': 'https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals'
        },
        {
            'title': 'Generation adidas Cup: Orlando City highlight U18 Best XI',
            'old_url': 'https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-orlando-city-highlight-u18-best-xi',
            'new_url': 'https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-orlando-city-highlight-u18-best-xi'
        }
    ]

    for i, pair in enumerate(url_pairs, 1):
        print(f"{i}. {pair['title']}")
        print(f"   OLD: {pair['old_url']}")
        print(f"   NEW: {pair['new_url']}")
        print()

    print("=" * 60)
    print("🔍 WITHOUT URL NORMALIZATION:")
    print("These would be treated as 3 modified articles (false positive)")
    print()

    # Show what happens without normalization
    print("Hash without normalization:")
    old_articles = [{'title': pair['title'], 'link': pair['old_url']} for pair in url_pairs]
    new_articles = [{'title': pair['title'], 'link': pair['new_url']} for pair in url_pairs]

    # Temporarily disable normalization to show the difference
    import scripts.check_content_changes
    original_setting = scripts.check_content_changes.ENABLE_URL_NORMALIZATION
    scripts.check_content_changes.ENABLE_URL_NORMALIZATION = False

    old_hash_no_norm = create_content_hash(old_articles)
    new_hash_no_norm = create_content_hash(new_articles)

    print(f"Old hash: {old_hash_no_norm}")
    print(f"New hash: {new_hash_no_norm}")
    print(f"Match: {old_hash_no_norm == new_hash_no_norm}")
    print()

    print("=" * 60)
    print("✅ WITH URL NORMALIZATION:")
    print("These are correctly identified as the same articles")
    print()

    # Re-enable normalization
    scripts.check_content_changes.ENABLE_URL_NORMALIZATION = original_setting

    old_hash_with_norm = create_content_hash(old_articles)
    new_hash_with_norm = create_content_hash(new_articles)

    print(f"Old hash: {old_hash_with_norm}")
    print(f"New hash: {new_hash_with_norm}")
    print(f"Match: {old_hash_with_norm == new_hash_with_norm}")
    print()

    # Show the normalized URLs
    print("Normalized URLs:")
    for pair in url_pairs:
        old_norm = normalize_mls_url(pair['old_url'])
        new_norm = normalize_mls_url(pair['new_url'])
        print(f"  {pair['title'][:50]}...")
        print(f"    Old normalized: {old_norm}")
        print(f"    New normalized: {new_norm}")
        print(f"    Match: {old_norm == new_norm}")
        print()

    print("=" * 60)
    print("📈 IMPACT:")
    print(f"Without normalization: {len(url_pairs)} false positive changes")
    print(f"With normalization: 0 false positives")
    print(f"Result: No unnecessary deployments when MLS changes URL paths!")
    print()

    # Test the full comparison
    print("🔬 FULL COMPARISON TEST:")
    changes = compare_articles(old_articles, new_articles)

    print(f"Changed: {changes['changed']}")
    print(f"Reason: {changes['reason']}")
    print(f"URL Normalized: {len(changes['details']['url_normalized'])}")
    print(f"Modified: {len(changes['details']['modified'])}")

    if changes['details']['url_normalized']:
        print("\nURL Normalized Articles:")
        for article in changes['details']['url_normalized']:
            print(f"  🔗 {article['title']}")
            print(f"     Previous: {article['prev_link']}")
            print(f"     New: {article['new_link']}")
            print(f"     Normalized: {article['normalized_link']}")

    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE!")
    print("URL normalization successfully prevents false positives when")
    print("MLS changes URL paths but articles remain the same content.")


if __name__ == "__main__":
    demo_url_normalization()
