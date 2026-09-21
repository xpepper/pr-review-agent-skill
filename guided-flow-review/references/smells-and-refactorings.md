# Code Smells and Refactoring Guide

Read this when checking a step's code for refactoring opportunities, or when
formulating a refactoring recommendation.

The aim is code that stays easy to change: suggest a refactoring when the change
introduces or worsens a smell and the refactoring has a concrete payoff. Every
smell here is a heuristic. The numbers are signals that make a smell worth a
look, not limits that make it a finding, and the project's documented
conventions override this guide.

## Modularity (look here first)

These smells cost the most over time, so they outrank local tidiness.

- **Divergent change / large module**:
  - *Signal*: One file or class changed for several unrelated reasons, or
    accumulating disparate responsibilities (e.g., HTTP handling, domain
    validation, and persistence together).
  - *Refactoring*: Split Module / Extract Class, so each part changes for one
    reason.
- **Shotgun surgery**:
  - *Signal*: One logical change forces scattered edits across many files in
    the diff.
  - *Refactoring*: Move Function / Move Field to gather what changes together
    into one module.
- **Feature envy**:
  - *Signal*: A function reaches into another object's fields or getters more
    than its own data.
  - *Refactoring*: Move Function onto the object that holds the data.
- **Shallow module / thin pass-through**:
  - *Signal*: A function or class whose interface is as complex as its
    implementation, mostly delegating onward.
  - *Refactoring*: Inline Function / Class, or deepen the module by hiding the
    orchestration behind it.
- **Speculative generality**:
  - *Signal*: Unused parameters, extension hooks, or abstractions with one
    implementer, added for needs the change does not have.
  - *Refactoring*: Inline / Collapse Hierarchy, remove unused parameters.

## Domain concepts

- **Primitive obsession**:
  - *Signal*: Raw strings, numbers, or tuples standing in for a domain concept
    (email, currency, ID, range) that keeps being validated or parsed.
  - *Refactoring*: Replace Primitive with Object / Value Type.
- **Data clumps / long parameter list**:
  - *Signal*: The same fields or parameters travelling together; a signature
    growing past three or four parameters is a hint.
  - *Refactoring*: Introduce Parameter Object / Preserve Whole Object.

## Duplication

- **Duplicated logic**:
  - *Signal*: The same logic shape in more than one hunk, function, or test,
    such as copied transformations or error handling.
  - *Refactoring*: Extract Function and call it from both places.
- **Alternative implementations with different interfaces**:
  - *Signal*: Two modules doing essentially the same work behind different
    signatures.
  - *Refactoring*: Rename, Extract Interface, or unify behind one adapter.

## Readability

Usually `nit` material; fold several into one point.

- **Long function**:
  - *Signal*: A function mixing levels of abstraction or doing more than one
    task; length (roughly 25+ lines) is only a hint.
  - *Refactoring*: Extract Function; separate orchestration from computation.
- **Deep nesting / complex conditional**:
  - *Signal*: Nesting three or more levels deep, or compound boolean
    expressions inlined in control flow.
  - *Refactoring*: Guard clauses; Decompose Conditional into named predicates.
- **Mysterious name**:
  - *Signal*: A name that does not reveal what the thing does or holds.
  - *Refactoring*: Rename; if no honest name comes, the design is murky, which
    may point to a modularity smell above.
- **Dead code**:
  - *Signal*: Commented-out blocks, unreachable branches, uncalled helpers.
  - *Refactoring*: Delete; git history keeps it.

## Formulating a refactoring point

Use the normal severity tags (`should` or `nit`, `blocking` only when the smell
makes the change unsafe to merge) and include:

1. **Smell as a possibility**: "Possible Feature Envy", with `file:line`
   evidence.
2. **Payoff**: what becomes easier to change, test, or understand afterwards.
   No concrete payoff means taste: label it or drop it.
3. **Move**: the named refactoring and where it leads.

```markdown
2. **[should] Possible Feature Envy: `invoiceTotal` works on `Order` internals**
   - Evidence: `src/billing.ts:30-48` reads six `order.*` fields and none of
     its own.
   - Payoff: pricing rules live with `Order`, so the next rule touches one
     module.
   - Recommendation: move the computation to `Order.total()`.
```

Routing:
- **Refactorings**: the default; worthwhile in this code area but safe to
  defer.
- **Follow-up**: a pre-existing smell, or one whose fix reaches beyond the
  change.
- **Open**: only when the smell makes the change unsafe to merge.
