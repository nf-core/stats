---
name: Test Evidence Page
description: Test Evidence.dev pages with agent-browser
---

# Test Evidence Page

## When to Use
- Verifying page renders correctly after changes
- Checking deploy previews for PR validation
- Debugging chart/component errors

## Prerequisites
- `bunx agent-browser` available (no install needed)
- For local: MotherDuck credentials set

## Testing Deploy Preview

```bash
# Open page
bunx agent-browser open "https://deploy-preview-<PR#>--nf-core-stats.netlify.app/<path>/"

# Get accessibility tree (for AI analysis)
bunx agent-browser snapshot

# Take screenshot
bunx agent-browser screenshot /tmp/page.png

# Close browser
bunx agent-browser close
```

## Testing Local Dev Server

```bash
# Start server (needs MotherDuck token)
export MOTHERDUCK_TOKEN="your-token"
npm run sources
npm run dev &

# Test page
bunx agent-browser open "http://localhost:3000/<path>/"
bunx agent-browser snapshot
bunx agent-browser screenshot /tmp/local.png
bunx agent-browser close
```

## Common Commands

| Command | Description |
|---------|-------------|
| `open <url>` | Navigate to URL |
| `snapshot` | Get accessibility tree |
| `screenshot <path>` | Save screenshot |
| `scroll down <px>` | Scroll down |
| `click <selector>` | Click element |
| `close` | Close browser |

## Debugging Tips

1. Use `snapshot` to check element presence and text
2. Screenshot captures visual errors (empty charts, error badges)
3. Check for "error" text in BigValue components
4. Verify date columns render correctly in charts

## Example Workflow

```bash
# Quick visual check
bunx agent-browser open "https://deploy-preview-111--nf-core-stats.netlify.app/code/strict_syntax/"
bunx agent-browser screenshot /tmp/check.png
bunx agent-browser close
```
