# Code Smells and Refactoring Guide

Read this when evaluating code during a review step, or when formulating
refactoring recommendations for findings.

Maintainability, readability, and structural hygiene are first-class review
concerns. Review code structure mercilessly: if a function is oversized, logic is
duplicated, names obscure intent, or abstractions are shallow, surface it as a
concrete finding with `file:line` evidence and a specific refactoring
recommendation.

## Smell baseline and heuristics

### 1. Bloaters (size and complexity)

- **Long method / function**:
  - *Heuristic*: A function exceeding ~25 lines, spanning multiple levels of
    abstraction, or doing more than one logical task.
  - *Refactoring*: Extract Function / Method. Separate orchestration from
    computation.
- **Large class / module / file**:
  - *Heuristic*: A file or class accumulating disparate responsibilities (e.g.,
    mixing HTTP handling, domain validation, and database operations).
  - *Refactoring*: Extract Class / Module. Group related operations around
    shared state or cohesion boundaries.
- **Long parameter list**:
  - *Heuristic*: More than 3-4 parameters passed to a function, especially
    primitives that travel together.
  - *Refactoring*: Introduce Parameter Object / Preserve Whole Object.

### 2. Duplication and redundancy

- **Duplicated logic**:
  - *Heuristic*: Identical or near-identical code blocks across hunks,
    functions, or test cases; copy-pasted payload transformations or error
    handling.
  - *Refactoring*: Extract Function, Form Template Method, or Pull Up Method.
- **Alternative implementations with different interfaces**:
  - *Heuristic*: Two classes or modules doing essentially the same work but with
    different method signatures.
  - *Refactoring*: Rename Methods, Extract Interface, unify with an Adapter.

### 3. Readability and cognitive load

- **Deep nesting**:
  - *Heuristic*: Conditionals or loops nested 3 or more levels deep.
  - *Refactoring*: Replace Nested Conditional with Guard Clauses (early returns);
    Extract Function.
- **Mysterious / murky names**:
  - *Heuristic*: Single-letter variables outside trivial loop counters, generic
    names (`data`, `result`, `item`, `temp`, `handler`), or names that obscure
    intent.
  - *Refactoring*: Rename Variable / Function / Type to reveal domain intent and
    invariants.
- **Complex boolean logic**:
  - *Heuristic*: Compound boolean expressions with multiple `&&`, `||`, and `!`
    conditions inlined in control structures.
  - *Refactoring*: Decompose Conditional into well-named explanatory boolean
    variables or helper predicate functions.

### 4. Coupling and responsibility leaks

- **Feature envy**:
  - *Heuristic*: A function or method that frequently reaches into another
    object's fields or getters rather than its own data.
  - *Refactoring*: Move Method / Move Field onto the object that holds the data.
- **Primitive obsession**:
  - *Heuristic*: Using raw strings, integers, or tuples to represent core domain
    concepts (e.g., unvalidated email strings, currencies, IDs, ranges) instead
    of dedicated value objects.
  - *Refactoring*: Replace Primitive with Object / Value Type.
- **Data clumps**:
  - *Heuristic*: The same group of fields or parameters always appearing
    together across functions or data structures.
  - *Refactoring*: Extract Class / Parameter Object.

### 5. Architectural and interface smells

- **Shallow module / thin pass-through**:
  - *Heuristic*: A function or class whose interface is as complex as its
    implementation, mostly just delegating onward with little added leverage.
  - *Refactoring*: Inline Class / Function, or deepen the module by hiding
    internal orchestration.
- **Speculative generality**:
  - *Heuristic*: Unused parameters, premature extension hooks, abstract base
    classes with only one implementer, or generic abstractions created for
    hypothetical futures.
  - *Refactoring*: Inline / Collapse Hierarchy, remove unused parameters.
- **Dead or zombie code**:
  - *Heuristic*: Commented-out code blocks, unreachable branches, uncalled
    private helpers.
  - *Refactoring*: Delete immediately. Git history preserves past code.

## Formulating a refactoring finding

Every refactoring point must include:
1. **Tag**: `[refactor]` (or `[nit, refactor]` if minor).
2. **Specific evidence**: Exact `path/to/file:line` or range.
3. **Specific smell**: Name the smell from this guide.
4. **Concrete action**: Name the exact refactoring move and proposed outcome.

Example:

```markdown
1. **[refactor] Deep nesting and high cognitive complexity in `calculateDiscount`**
   - Evidence: `src/pricing.ts:42-88` (4 levels of nested `if`/`else` branches).
   - Smell: Deep Nesting / Complex Conditional.
   - Recommendation: Replace nested conditionals with guard clauses and extract `tierMultiplier()` helper.
```

Routing:
- Route to **Refactorings (this PR/change or later)** when it is safe to defer
  or should be addressed after the core flow is reviewed.
- Route to **Open** only if the smell creates active maintainability risk that
  directly blocks the change from merging.
