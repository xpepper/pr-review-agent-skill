# PR Preparation and Review Agent Skills

A collection of [Agent Skills](https://agentskills.io) for preparing changes and
automating pull-request review workflows.
Compatible with Claude Code, GitHub Copilot, Cursor, Windsurf, and 30+ other agents.

## Skills

### Prepare Review Commits

Turns the current uncommitted diff into a logical sequence of validated,
self-contained Conventional Commits, ready for pull-request review. Never
rewrites history or pushes.

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits
```

[See skill README →](prepare-review-commits/README.md)

---

### PR Review Loop

Addresses all open PR review comments one at a time using an opinionated, resumable workflow.
Works with any reviewer (human or bot).

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop
```

[See skill README →](pr-review-loop/README.md)

---

### Copilot Review Loop

An in-session Copilot-driven review loop: triggers Copilot review, addresses
its feedback one comment at a time, and re-triggers Copilot until all critical
issues are resolved or 2 cycles are complete. Runs within a single agent session.

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/copilot-review-loop
```

[See skill README →](copilot-review-loop/README.md)

---

### Ralph Wiggum Loop

The [Ralph Wiggum pattern](https://ghuntley.com/ralph/): an external shell loop
that spawns a fresh agent session for each PR comment. Drop `CODE_REVIEW_PLAN.md`
into your project root and run the loop — each invocation fixes one comment, then
stops. Works with any agent (Claude, Codex, Cursor, etc.).

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/ralph-wiggum-loop
```

[See skill README →](ralph-wiggum-loop/README.md)

---

## Requirements

- `gh` CLI (recommended) or a GitHub token for REST API fallback
- Git

## Development

### Skill structure

Each skill is a directory containing:

```
<skill-name>/
  SKILL.md          # required — skill definition with YAML frontmatter
  README.md         # recommended — user-facing documentation
  references/       # optional — supporting reference documents
```

The `SKILL.md` frontmatter must include at minimum `name` and `description`. See existing skills for the full set of supported fields (`license`, `compatibility`, `metadata`, `allowed-tools`).

### Packaging

After adding or modifying a skill, regenerate the `.skill` package:

```bash
./package-skill.sh
```

The script auto-discovers all directories that contain a `SKILL.md` and packages each one. Generated `.skill` files are gitignored (build artifacts).

### Testing a skill

After pushing changes, verify a skill installs and removes correctly:

```bash
# Install (--yes skips interactive prompts)
npx skills add xpepper/pr-review-agent-skill/<skill-name> --yes

# Verify the skill description appears and the install path looks correct, then remove
npx skills remove <skill-name>
```

Note: without `--global`, skills are installed project-locally into `.agents/skills/` (gitignored).

## License

MIT
