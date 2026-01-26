# Troubleshooting Guide for MLS NEXT RSS Scraper

## False Positive Change Detection

If you're experiencing deployments that run even when there are no new articles, this guide will help you identify and resolve the issue.

## Important: What Triggers Deployments

**Only the following changes trigger deployments:**

- **New articles added** (title + link)
- **Articles removed** (title + link)
- **Article titles changed**
- **Article links changed**

**The following changes do NOT trigger deployments:**

- ❌ Article description updates
- ❌ RSS metadata changes (timestamps, build dates)
- ❌ Text formatting differences
- ❌ Image URL changes
- ❌ Article order changes (unless articles are added/removed)

This is intentional because RSS readers like Reeder don't show description updates once articles are downloaded.

## Common Causes of False Positives

1. **RSS Metadata Changes**: The RSS feed includes timestamps like `lastBuildDate` that change every run
2. **Text Formatting Differences**: Minor whitespace or HTML tag differences
3. **Image URL Changes**: Dynamic image URLs that change between runs
4. **Article Order Changes**: Articles appearing in different order due to sorting
5. **Description Updates**: Article descriptions being updated on the source website (ignored)

## Debugging Tools

### 1. Enhanced Change Detection Script

The improved `scripts/check_content_changes.py` now provides detailed information about what changed:

```bash
python scripts/check_content_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml
```

This will show:

- Whether content actually changed
- How many articles were added/removed/modified
- **Exact article details** that changed (title, link, description preview)
- Content hashes for comparison

### 2. RSS Debug Tool

Use the new `scripts/debug_changes.py` to analyze RSS files in detail:

```bash
# Analyze current RSS file
python scripts/debug_changes.py output/mls_next_news.xml

# Compare with previous version
python scripts/debug_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml
```

This tool provides:

- Detailed RSS file analysis
- Metadata comparison
- Article-by-article comparison
- Content hash analysis
- Clear indication of what's different

### 3. Enhanced Logging

The main scraper now provides detailed logging about:

- Articles being extracted
- Duplicate detection
- Final article summary
- Processing steps

## GitHub Actions Improvements

The workflow now captures and displays:

- Detailed change reasons
- Article counts (added/removed/modified)
- **Exact article details** that changed
- Better logging of what triggered deployment
- Change summaries in deployment logs

## How to Investigate False Positives

### Step 1: Check the GitHub Actions Logs

Look for the "Change Detection Summary" and "DETAILED ARTICLE CHANGES" sections in your workflow run. They will show:

- Whether changes were detected
- The specific reason
- **Exact article titles and links** that changed
- Article counts

### Step 2: Use the Debug Tool

If you suspect a false positive, run the debug tool:

```bash
# After a run that deployed unnecessarily
python scripts/debug_changes.py output/mls_next_news.xml ../rss-feeds-checkout/mls_next_news.xml
```

### Step 3: Analyze the Output

Look for:

- **Content hashes**: If they're different, something actually changed
- **Article differences**: Check if articles were added/removed/modified
- **Metadata changes**: These shouldn't trigger deployments
- **Description changes**: These are ignored and won't trigger deployments

### Step 4: Check for Common Issues

1. **Article titles updated**: The source website might have updated article titles
2. **Article links changed**: Article URLs might have been updated
3. **New articles added**: Even if they're not "news", they might be new content
4. **Articles removed**: Old articles might have been taken down

## Example Debug Output

```
🔍 MLS NEXT RSS Change Debug Tool
Focus: Title and Link Changes Only (Descriptions Ignored)
================================================================================

📁 Current RSS File Analysis:
   File: output/mls_next_news.xml
   Articles: 15
   Content Hash: a1b2c3d4e5f6...
   Title: MLS NEXT News
   Last Build: Mon, 01 Jan 2024 12:00:00 GMT
   Pub Date: Mon, 01 Jan 2024 12:00:00 GMT

📰 First 3 Articles:
   1. ⭐ New MLS NEXT Academy Announced
      Link: https://www.mlssoccer.com/mlsnext/news/new-academy
      Description: Major League Soccer has announced a new academy...

🔍 Comparing RSS files:
   Current: output/mls_next_news.xml
   Previous: ../rss-feeds-checkout/mls_next_news.xml

📊 File Analysis:
   Current: 15 articles, hash: a1b2c3d4e5f6...
   Previous: 15 articles, hash: f6e5d4c3b2a1...

📋 Metadata Comparison:
   ❌ last_build:
      Current: Mon, 01 Jan 2024 12:00:00 GMT
      Previous: Mon, 01 Jan 2024 11:30:00 GMT
   ❌ pub_date:
      Current: Mon, 01 Jan 2024 12:00:00 GMT
      Previous: Mon, 01 Jan 2024 11:30:00 GMT

❌ Content hashes differ - content has changed

📝 Article Comparison:
   ➕ Added articles (1):
      • New MLS NEXT Academy Announced
        Link: https://www.mlssoccer.com/mlsnext/news/new-academy
        Description: Major League Soccer has announced a new academy...
```

## Resolving False Positives

### 1. Whitelist Known Changes

If certain types of changes shouldn't trigger deployments, modify the change detection logic in `scripts/check_content_changes.py`.

### 2. Adjust Change Sensitivity

You can make the change detection more or less sensitive by modifying what's included in the content hash.

### 3. Add Exclusions

Consider excluding certain fields or articles from change detection if they're known to change frequently.

## Best Practices

1. **Always check the logs** when deployments seem unnecessary
2. **Use the debug tools** to understand what changed
3. **Monitor article sources** for unexpected updates
4. **Review change detection logic** if false positives persist
5. **Document known issues** for future reference

## Getting Help

If you continue to experience false positives:

1. Run the debug tools and save the output
2. Check the GitHub Actions logs for the specific run
3. Compare the RSS files manually if needed
4. Consider if the changes are actually meaningful

Remember: The goal is to deploy only when there's meaningful new content (new articles, title changes, or link changes), not when metadata or description formatting changes.
