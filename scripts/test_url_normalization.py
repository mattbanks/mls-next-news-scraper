#!/usr/bin/env python3
"""
Test script for URL normalization functionality.
Tests the normalize_mls_url function with various MLS URL patterns.
"""

import sys
import os

# Add the parent directory to the path so we can import the function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.check_content_changes import normalize_mls_url


def test_url_normalization():
    """Test various URL patterns to ensure normalization works correctly."""

    test_cases = [
        # Test cases from the logs - these should normalize to the same value
        {
            "name": "All-Star Game URL change",
            "url1": "https://www.mlssoccer.com/allstar/2025/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west",
            "url2": "https://www.mlssoccer.com/mlsnext/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west",
            "should_match": True
        },
        {
            "name": "Generation Adidas Cup URL change",
            "url1": "https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals",
            "url2": "https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals",
            "should_match": True
        },
        {
            "name": "Different articles should not match",
            "url1": "https://www.mlssoccer.com/mlsnext/news/article-1",
            "url2": "https://www.mlssoccer.com/mlsnext/news/article-2",
            "should_match": False
        },
        {
            "name": "News listing pages should not be normalized",
            "url1": "https://www.mlssoccer.com/mlsnext/news/",
            "url2": "https://www.mlssoccer.com/mlsnext/news/",
            "should_match": True
        },
        {
            "name": "Non-MLS URLs should not be normalized",
            "url1": "https://example.com/article",
            "url2": "https://example.com/article",
            "should_match": True
        }
    ]

    print("Testing URL normalization function...")
    print("=" * 60)

    all_passed = True

    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"URL 1: {test_case['url1']}")
        print(f"URL 2: {test_case['url2']}")

        norm1 = normalize_mls_url(test_case['url1'])
        norm2 = normalize_mls_url(test_case['url2'])

        print(f"Normalized 1: {norm1}")
        print(f"Normalized 2: {norm2}")

        do_match = norm1 == norm2
        expected = test_case['should_match']

        if do_match == expected:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_passed = False

        print(f"Match: {do_match} (Expected: {expected}) {status}")

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")

    return all_passed


def test_specific_mls_patterns():
    """Test specific MLS URL patterns we've seen in the logs."""

    print("\nTesting specific MLS URL patterns from logs...")
    print("=" * 60)

    # These are the actual URLs from the logs
    url_pairs = [
        (
            "https://www.mlssoccer.com/allstar/2025/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west",
            "https://www.mlssoccer.com/mlsnext/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west"
        ),
        (
            "https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals",
            "https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals"
        ),
        (
            "https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-orlando-city-highlight-u18-best-xi",
            "https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-orlando-city-highlight-u18-best-xi"
        )
    ]

    for i, (url1, url2) in enumerate(url_pairs, 1):
        print(f"\nPair {i}:")
        norm1 = normalize_mls_url(url1)
        norm2 = normalize_mls_url(url2)

        print(f"Original 1: {url1}")
        print(f"Original 2: {url2}")
        print(f"Normalized 1: {norm1}")
        print(f"Normalized 2: {norm2}")

        if norm1 == norm2:
            print("✅ URLs normalize to the same value (same article)")
        else:
            print("❌ URLs normalize to different values (different articles)")


if __name__ == "__main__":
    print("MLS URL Normalization Test Suite")
    print("=" * 60)

    # Run the general test suite
    test_url_normalization()

    # Run the specific MLS pattern tests
    test_specific_mls_patterns()

    print("\nTest suite completed!")
