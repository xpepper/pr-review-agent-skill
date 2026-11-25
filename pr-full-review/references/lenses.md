# Review Lenses

Detailed instructions for each of the four lenses run in Step 2 of
`pr-full-review`. When a matching companion skill is installed, honor its latest
rules; otherwise these specifications are self-contained.

## Lens 1: Standards (Code Review, Axis 1)

Run in a fresh-context subagent when supported. Give it:

- The diff command (`git diff <merge-base>...HEAD`) and commit list
  (`git log <merge-base>..HEAD --oneline`).
- Every discovered repository standards file (`AGENTS.md`, `CLAUDE.md`,
  `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `GLOSSARY.md`, testing/code-pattern
  docs, and package guides for touched workspaces).
- The **Fowler smell baseline** below, pasted in full so the subagent does not
  rely on memory:
  - **The repo overrides.** A documented repo standard always wins; suppress any
    smell that a repo standard endorses.
  - **Always a judgement call.** Baseline smells are heuristics ("possible
    Feature Envy"), never hard violations. Skip anything tooling already
    enforces (formatters, linters, license/unused-dep checks).
  - **Mysterious Name**: name does not reveal what it does or holds -> rename
    it; if no honest name comes, the design is murky.
  - **Duplicated Code**: same logic shape in more than one hunk or file ->
    extract the shared shape.
  - **Feature Envy**: method reaches into another object's data more than its
    own -> move it onto that data.
  - **Data Clumps**: same few fields or params keep travelling together ->
    bundle them into one type.
  - **Primitive Obsession**: primitive or string standing in for a domain
    concept -> give it a small type.
  - **Repeated Switches**: same switch/if-cascade recurs across the change ->
    replace with polymorphism or one shared map.
  - **Shotgun Surgery**: one logical change forces scattered edits across many
    files -> gather what changes together.
  - **Divergent Change**: one file or module edited for several unrelated
    reasons -> split by reason to change.
  - **Speculative Generality**: abstractions, parameters, or hooks added for
    needs the spec does not have -> delete and inline.
  - **Message Chains**: long `a.b().c().d()` navigation callers should not
    depend on -> hide behind one method.
  - **Middle Man**: class or function that mostly delegates onward -> remove
    indirection.
  - **Refused Bequest**: implementer ignores or overrides most inherited
    behavior -> replace inheritance with composition.

**Subagent brief:** Report, per file/hunk: (a) every place the diff violates a
documented standard (cite file + rule), plus any stale comments or broken test
mocks left in or adjacent to the diff; and (b) any baseline smell spotted (name
it and quote the hunk). Separate hard violations from judgement calls. Under 400
words.

## Lens 2: Spec (Code Review, Axis 2)

Run in a fresh-context subagent in parallel with Standards when supported. Give
it:

- The diff command and commit list.
- The full PR body (or the alternative spec file/issue the user supplied).

**Subagent brief:** Verify every requirement, table, boundary condition,
non-goal, and Evidence claim in the spec against the diff and surrounding code
(including migrations, schemas, and callers). Report:
(a) requirements that are missing or partial;
(b) behavior in the diff that was not asked for (scope creep);
(c) requirements that look implemented but have edge-case bugs, subtle contract
mismatches, or inaccurate Evidence claims. Quote the spec line for each finding.
Under 400 words.

If no spec exists (empty PR body and no linked spec/issue), skip this subagent
and note "no spec available" under `## Spec`.

## Lens 3: Balanced Coupling / Modularity

Run in a fresh-context subagent in parallel with Standards and Spec when
supported. Scope strictly to the boundaries created or modified by the PR and
their direct callers/callees. Do **not** launch an interactive whole-codebase
review questionnaire.

Evaluate each modified integration along Vlad Khononov's three dimensions:

- **Integration strength** (shared knowledge, strongest to weakest): Intrusive
  (private internals/DB schemas), Functional (shared/duplicated business rules
  or implicit preconditions), Model (shared domain/storage structs), Contract
  (explicit DTO/facade/port encapsulating internals). Note implicit vs explicit
  knowledge and connascence where relevant.
- **Distance** (relative to the observed level): intra-module, cross-module,
  cross-crate/package, cross-service, plus team/runtime distance.
- **Essential volatility** (from the business domain, not commit count): Core
  (high volatility), Supporting (low volatility), Generic (low functional
  volatility, variable provider volatility).

Apply the balance rule: `BALANCE = (STRENGTH XOR DISTANCE) OR NOT VOLATILITY`.
Flag only integrations that are **unbalanced and volatile**:

- High strength + high distance + high volatility (tight coupling in an evolving
  area).
- Low strength + low distance (low cohesion, unrelated responsibilities bundled
  into one growing module).

Ground every finding in exact `file:line` references and propose the smallest
structural fix along with its trade-off. Under 400 words.

## Lens 4: Code Refactor Review + Duplication Review

### 4a. Code Refactor Review

Inspect the full diff and trace the call stack / data flow before judging
isolated lines. Check:

1. **Reuse existing code (search in both directions)**: for every new function,
   type, or helper, search the repo by **concept** (synonyms and glossary
   terms), by **shape** (same inputs/outputs or distinctive calls), and by
   **neighborhood** (sibling files and imported modules). Check both whether
   new code duplicates existing code and whether a new helper could replace
   older inline logic. Recommend merging only when both share **intent**, not
   merely structure.
2. **Codebase consistency**: file placement, naming, error/result types, and
   sibling conventions.
3. **Composition and boundaries**: single level of abstraction, no grab-bag
   modules, no parameter sprawl, no unnecessary wrapper chains.
4. **Slop detection**: comment slop (obvious or stale comments), helper slop,
   type slop, compatibility cruft, unrelated diff churn.
5. **Minimality**: prefer deleting code over adding indirection; keep fixes
   proportional.

Assign a verdict (`clean`, `mostly clean`, or `needs cleanup`). Put anything
whose fix would touch unchanged files under an **Outside this diff** section.

### 4b. Duplication Review (`duplication-review` / `jscpd`)

Locate `duplication-review`'s bundled clone script on disk (important because
`duplication-review` sets `disable-model-invocation: true` and may not appear in
auto-loaded skill lists):

```bash
for candidate in \
  ".agents/skills/duplication-review/scripts/clones.mjs" \
  "$HOME/.agents/skills/duplication-review/scripts/clones.mjs" \
  "$HOME/.claude/skills/duplication-review/scripts/clones.mjs" \
  "$HOME/.gemini/config/skills/duplication-review/scripts/clones.mjs"; do
  if [ -f "$candidate" ]; then echo "$candidate"; break; fi
done
```

If found (and Node 22+ is available), run it from the repository root:

```bash
node "<clones.mjs>" --base "origin/${base}"
```

If `clones.mjs` is not installed, check whether the repository configures a
clone detector (`jscpd`, PMD CPD, etc.) that runs without installing packages;
if none is available, state that in one line and rely on the manual reuse search
in 4a.

When `clones.mjs` runs:

1. Record `jscpd` version, `totals` (`clones`, `duplicatedLines`, `percentage`,
   `kinds`), and `renamed.clones`.
2. Open and read every fragment of every family in `families` (never rule from
   line counts alone). Merge families when one abstraction retires both; split a
   family when overlapping fragments belong to different concepts.
3. Rule every family:
   - **Extract**: fragments share one reason to change and call sites read
     better with the named element (give its domain name, path, retired clones,
     and estimated lines after).
   - **Tolerate**: accidental similarity or distinguishing test/config intent
     (give the one-line reason).
4. Check `pre-existing-edited` clones to confirm whether the other side needs
   the same edit.
5. Report `Extract` entries first, then `Tolerate` entries, followed by
   `bystanders.largest` (one line each) and a count of the remaining bystanders
   as untouched follow-ups.
