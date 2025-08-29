# URL Normalization Solution for MLS NEXT News Scraper

## Problem Description

The MLS NEXT news scraper was experiencing false positive "changes" when MLS changed URL paths for articles without changing the actual content. This caused unnecessary deployments and RSS feed updates.

### Example from Logs

The logs showed these URL changes for the same articles:

**Before (Previous RSS):**

- `https://www.mlssoccer.com/allstar/2025/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west`
- `https://www.mlssoccer.com/generation-adidas-cup/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals`

**After (New RSS):**

- `https://www.mlssoccer.com/mlsnext/news/2025-mls-next-all-star-game-east-snatches-late-win-over-west`
- `https://www.mlssoccer.com/mlsnext/news/generation-adidas-cup-mls-champions-guaranteed-after-u16-u18-semifinals`

**Result:** 9 articles were flagged as "modified" even though they were the same content.

## Solution: URL Normalization

We implemented intelligent URL normalization that extracts the article identifier from URLs, ignoring the category path changes that MLS makes.

### How It Works

1. **URL Parsing**: Extracts the meaningful article slug from MLS URLs
2. **Pattern Recognition**: Handles various MLS URL patterns:
   - `/category/news/article-slug`
   - `/category/year/news/article-slug`
   - `/mlsnext/news/article-slug`
3. **Normalization**: Creates a consistent format: `mlssoccer.com/article/article-slug`
4. **Comparison**: Uses normalized URLs for change detection

### URL Patterns Handled

- ✅ `/allstar/2025/news/article-name` → `mlssoccer.com/article/article-name`
- ✅ `/generation-adidas-cup/news/article-name` → `mlssoccer.com/article/article-name`
- ✅ `/mlsnext/news/article-name` → `mlssoccer.com/article/article-name`
- ✅ `/category/year/news/article-name` → `mlssoccer.com/article/article-name`

## Implementation

### Files Modified

1. **`scripts/check_content_changes.py`** - Main change detection script with URL normalization
2. **`scripts/test_url_normalization.py`** - Test suite for URL normalization
3. **`scripts/test_change_detection.py`** - Test suite for change detection
4. **`scripts/demo_url_normalization.py`** - Demonstration script
5. **`README.md`** - Updated documentation

### Key Functions

```python
def normalize_mls_url(url: str) -> str:
    """Normalize MLS URLs to detect when articles are the same despite URL path changes."""

def create_content_hash(articles):
    """Create a hash based on article content (title and normalized link only)."""

def compare_articles(prev_articles, new_articles):
    """Compare articles and return detailed change information."""
```

### Configuration

```python
# Configuration
ENABLE_URL_NORMALIZATION = True  # Set to False to disable URL normalization
MLS_DOMAINS = ['mlssoccer.com', 'www.mlssoccer.com']  # MLS domains to normalize
```

## Testing

### Run Test Suite

```bash
# Test URL normalization
python scripts/test_url_normalization.py

# Test change detection
python scripts/test_change_detection.py

# See the demo
python scripts/demo_url_normalization.py
```

### Test Results

**Without URL Normalization:**

- Old hash: `b8d171844b3ab4ce0fc14496dc5bd89af241c9f9210e179f26785d61bed9c1c2`
- New hash: `3b0bdf56f754fb30c9211cb3f10a3f51bd1588c2bb7e8059eda45af3a54fd309`
- **Result:** False positive - 3 articles flagged as modified

**With URL Normalization:**

- Old hash: `b2e0a454c3325ef6373084851fdffb254f6681631cba624aefbdb2e7c2520890`
- New hash: `b2e0a454c3325ef6373084851fdffb254f6681631cba624aefbdb2e7c2520890`
- **Result:** No false positives - articles correctly identified as the same

## Benefits

1. **Eliminates False Positives**: No more unnecessary deployments when MLS changes URL paths
2. **Maintains Accuracy**: Still detects real content changes (new articles, removed articles, title changes)
3. **Configurable**: Can be disabled if needed
4. **Well Tested**: Comprehensive test suite ensures reliability
5. **Transparent**: Clear logging shows when URL normalization occurs

## Usage

### Basic Change Detection

```bash
python scripts/check_content_changes.py output/mls_next_news.xml
```

### Compare with Previous Version

```bash
python scripts/check_content_changes.py output/mls_next_news.xml previous_version.xml
```

### Disable URL Normalization

Set `ENABLE_URL_NORMALIZATION = False` in `scripts/check_content_changes.py`

## Output Examples

### URL Normalization Detected

```
=== URL NORMALIZED ARTICLES ===
🔗 2025 MLS NEXT All-Star Game: East snatches late win over West
   Link: https://www.mlssoccer.com/allstar/2025/news/... → https://www.mlssoccer.com/mlsnext/news/...
   Normalized: mlssoccer.com/article/2025-mls-next-all-star-game-east-snatches-late-win-over-west
```

### Change Detection Results

```
Changed: false
Reason: No content changes detected (URLs normalized: 3 article(s))
URL Normalized: 3
Modified: 0
```

## Future Enhancements

1. **Additional URL Patterns**: Add support for more MLS URL structures
2. **Machine Learning**: Train models to recognize article similarity beyond just URLs
3. **Content Fingerprinting**: Hash article content to detect when articles are truly the same
4. **Configuration File**: Move settings to a separate config file
5. **Metrics**: Track how often URL normalization prevents false positives

## Troubleshooting

### URL Normalization Not Working

1. Check that `ENABLE_URL_NORMALIZATION = True`
2. Verify URLs contain `mlssoccer.com` domain
3. Run test suite to verify functionality

### False Negatives

1. Ensure URL patterns are correctly handled
2. Check that article slugs are properly extracted
3. Review test cases for edge cases

### Performance Issues

1. URL normalization is lightweight and shouldn't impact performance
2. If issues occur, consider caching normalized URLs

## Conclusion

The URL normalization solution successfully addresses the false positive problem by:

- **Intelligently parsing** MLS URLs to extract article identifiers
- **Normalizing paths** to focus on content rather than structure
- **Maintaining accuracy** for real content changes
- **Providing transparency** through detailed logging
- **Offering flexibility** through configuration options

This solution ensures that the MLS NEXT news scraper only deploys when there are actual content changes, not when MLS reorganizes their URL structure.
