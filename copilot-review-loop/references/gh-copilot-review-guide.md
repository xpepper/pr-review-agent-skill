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
`copilot[bot]` review comments appear:

```bash
# Count current Copilot comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '[.[] | select(.user.login == "copilot[bot]") | select(.resolved == false)] | length'
```

Poll every 15 seconds. After 3 minutes with no new comments, stop and report timeout.

## Identifying Copilot comments

Filter by reviewer login `copilot[bot]`:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | select(.user.login == "copilot[bot]") | select(.resolved == false)'
```
