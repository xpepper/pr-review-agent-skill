# gh-copilot-review Extension Guide

## Purpose

This guide explains how to trigger a GitHub Copilot review from the CLI,
which is the key mechanism powering the Copilot Review Loop.

## Recommended: gh-copilot-review extension

Install once:
```bash
gh extension install ChrisCarini/gh-copilot-review
```

Trigger a Copilot review:
```bash
# By PR number
gh copilot-review 42

# By PR URL
gh copilot-review https://github.com/owner/repo/pull/42

# Current branch's PR (detect from git)
gh copilot-review
```

## Fallback: gh pr review --request

If the extension is not installed:
```bash
gh pr review --request copilot
```

Note: This may not work on all GitHub plans. The extension is more reliable.

## Detecting which to use

Check if the extension is installed:
```bash
gh extension list | grep copilot-review
```

If it appears in the output, use `gh copilot-review`. Otherwise fall back to `gh pr review --request copilot`.

## Waiting for Copilot to complete

After triggering, Copilot review takes 30–120 seconds. Poll until new
Copilot review comments appear:

```bash
# Count current Copilot comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '[.[] | select(.user.type == "Bot" and (.user.login | ascii_downcase | startswith("copilot")))] | length'
```

Record this count as the baseline. After triggering, poll until the count increases.

Poll every 15 seconds. After 3 minutes with no new comments, stop and report timeout.

## Identifying Copilot comments

GitHub posts Copilot's inline review comments as the bot user `Copilot`, and
the review itself as `copilot-pull-request-reviewer[bot]`. Neither is
`copilot[bot]`. Match any bot whose login starts with "copilot"
(case-insensitive), so a future rename does not break the filter:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | select(.user.type == "Bot" and (.user.login | ascii_downcase | startswith("copilot")))'
```

Fetch all Copilot comments. Use the count delta from polling to identify which are new in this review cycle.
