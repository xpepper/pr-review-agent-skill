# Guided review TODO template

Create this file after the review order is agreed, before reviewing the first
step. Keep it synchronized after every routing decision and completed fix.

```markdown
# <change identifier> review TODO (disposable, do not commit)

Review mode: <PR/branch | explicit range | working tree>
Branch: `<branch>`
Comparison: `<exact expression>`
Pinned base: `<sha or n/a>`
Starting HEAD: `<sha>`
Review TODO: `<path>`
Started: <YYYY-MM-DD>

## Open

## Refactorings (this PR/change or later)

## Missing tests

## Open questions (<owners or roles>)

## Follow-up (separate tickets)

## Done

## Review progress

- [ ] `<first runtime-flow file or file group>`
- [ ] `<next file or file group>`
- [ ] docs: `<documentation files>`
```

## Item form

Use one bold title followed by the minimum evidence needed to reconstruct the
decision:

```markdown
- [ ] **<one-line title>.** Evidence: `<file:line>` or `<command>` ->
      `<relevant output>`. Recommendation: <smallest justified action>.
      Dependencies: <supersedes/pairs with/blocked by, when relevant>.
      Decided <YYYY-MM-DD>: <decision, when resolved>.
```

Completed fixes include the subject so the record survives rewritten history:

```markdown
- [x] (`<sha>`) **`<commit subject>`** - <what the fix proved>.
```

In working-tree mode, use:

```markdown
- [x] (`uncommitted`) **<fix title>** - <verification performed>.
```

Record dropped points under their Review progress entry:

```markdown
- [x] `path/to/file`
  - Dropped point 2 on <YYYY-MM-DD>: <reason it is not worth changing>.
```

Never include credential values, tokens, private keys, or copied environment
file contents. Refer only to the path and variable/key name.
