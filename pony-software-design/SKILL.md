---
name: pony-software-design
description: Disciplines for software design work. Load when designing APIs, type systems, features, or system boundaries. Counters the tendency to retrieve familiar patterns instead of discovering what the problem actually needs. Has full (8-persona) and lightweight (5-persona) modes.
disable-model-invocation: false
---

# Software Design

Load this skill when doing design work — APIs, type systems, features, system
boundaries. The core problem it addresses: LLMs default to *retrieving*
familiar patterns from training data rather than *discovering* what a specific
problem needs. The result is designs that look right (they have the right nouns)
but weren't derived from the problem.

Design is the act of discovering what is needed. It's about finding surprising
affordances and avoiding candy-machine interfaces riddled with footguns.

Design is not a phase. It's a continuous loop: observe what you have, orient
against what you know, decide, act, then observe again. Every decision you make
reveals new information. That information might confirm prior decisions or
invalidate them. Either way, you have to look. "I already decided that" is never
a reason to skip re-evaluation — it was decided with less information than you
have now.

## Mode selection

The skill has two modes: **full** and **lightweight**. The orchestrator
selects the appropriate mode based on the criteria below and proceeds.
Report the mode choice when presenting results — the human can request
full mode if lightweight was used and they want deeper coverage.

**Full mode** is the default. Use it when:

- Defining new boundaries — a new subsystem, API surface, or type hierarchy
- Multiple ownership or abstraction decisions need to be made simultaneously
- There's genuine design space to explore — multiple viable approaches
- The design must be described from first principles, not as an extension of
  something that already exists

**Lightweight mode** is for bounded design work within established patterns:

- Adding a method to an existing API, a new variant in a type family, a new
  handler following established conventions
- The boundaries are already decided — you're filling in, not redrawing
- Consumer code patterns are already established by adjacent features
- The task can be described as "another X that does Y" where X already exists
  in the codebase

When in doubt, use full mode. Lightweight is appropriate when there's a
clear existing pattern being extended and the boundaries are already
decided.

## Process: full mode

Design work is where pattern-matching failures are most costly and hardest to
self-detect. A single agent applying design disciplines will still
pattern-match — the disciplines become post-hoc rationalizations for a
retrieved design rather than actual constraints on the exploration.

The full design process runs in two stages with a feedback loop. Load
`/pony-ensemble` for the mechanical process; the personas defined in this skill
replace the generic attention focuses.

### Relationship to Ensemble Workflow

This skill uses the ensemble workflow with domain-specific customizations.
Stage 1 (design) runs as a standard ensemble with 3 personas. Stage 2
(evaluation) runs as a second ensemble with 5 personas, using the Stage 1
synthesis output as its input. The two-stage loop and finding categorization
(Rejection/Adjustment/Tension) are additions specific to this skill — the
base ensemble protocol handles agent spawning, triage, and synthesis
mechanics.

### Orchestrator pre-spawn: understand the problem

Before spawning design personas, the orchestrator must decompose the problem
statement. Ask: "What are we trying to accomplish? What pain point does this
address?"

If the problem statement implies a solution rather than stating a problem —
"add convenience wrapper methods for X" rather than "users struggle with X
because Y" — peel it back to the underlying pain point. If you can't
confidently identify the pain point, ask the human. This is not a failure;
it's the most valuable question the orchestrator can ask, because every
persona will anchor on whatever framing they receive.

Brief personas with the actual problem. The original problem statement can be
included as context, but the briefing should lead with the pain point: what the
user is struggling with and why. This gives personas room to explore different
solutions rather than anchoring on the solution implied by the problem
statement.

### Stage 1: Design

Three design personas explore the problem space in parallel. Each applies all
the disciplines below but enters the problem from a different direction. The
decorrelation comes from where they start, not what they know. Persona
definitions are in `personas/design/`.

| File | Focus |
|------|-------|
| `consumer-first.md` | Starts from usage code, derives API from what makes call sites clean |
| `skeptic.md` | Questions every abstraction, tries to subtract, proposes the smallest design |
| `principle-checker.md` | Hard verification of each design principle with evidence |

### Orchestrator post-return: evaluate exploration quality

When personas return, the orchestrator evaluates the quality of exploration
before forwarding outputs to synthesis. Check:

- **Did the personas explore meaningfully different approaches?** Read each
  persona's "Key decisions / alternatives considered" section. If a persona
  only considered one interpretation of the problem and designed for it, the
  exploration was insufficient.
- **Did they all anchor on the same narrow interpretation?** If all three
  personas produced designs based on the same framing of the problem — e.g.,
  all three designed wrapper methods — the ensemble failed to decorrelate.
  The different entry points weren't enough to overcome the anchoring effect
  of the problem statement.
- **Is the reasoning for rejecting alternatives sound?** A persona that
  considered a wild idea and rejected it with good reasoning explored
  genuinely. A persona that listed an alternative and dismissed it in one
  sentence didn't.

If exploration quality is poor — narrow interpretation, insufficient
alternatives, weak rejection reasoning — don't forward to synthesis. Refine
the briefing: restate the problem more broadly, point out the anchoring you
observed, and ask the human to clarify if needed. Then re-spawn.

### Stage 1 synthesis

Stage 1 synthesis produces a candidate design using the standard ensemble
synthesis process. The synthesis should pay special attention to:

- Where the consumer-first designer's sketches conflict with the skeptic's
  subtractions — the tension usually reveals the right boundary
- Where the principle checker found a violation that the others missed —
  this is the highest-value finding
- Whether all three converged on the same abstraction — convergence from
  different starting points is strong signal
- **When the skeptic says "no value" and redirects**: The skeptic is the only
  persona whose job includes saying "this shouldn't exist." When the skeptic
  concludes the proposed design doesn't earn its keep and redirects toward a
  different problem, this is not a minority position to be outvoted because
  the other two produced designs. The other two will *always* produce a
  design — that's their job. Evaluate the skeptic's case on its merits. If
  the skeptic is right that the design is a thin wrapper, the synthesis
  output should adopt the skeptic's redirect as the foundation: "the
  proposed design doesn't earn its keep — here's the actual problem worth
  solving" becomes the candidate, not a blended version of the thin wrapper.

### Stage 2: Evaluation

Five evaluation personas stress-test the candidate design in parallel. Their
input is the Integrated Result from Stage 1 synthesis — the candidate design
with its consumer sketches, type definitions, and boundary decisions. They
evaluate these design artifacts, not implementation code. Persona definitions
are in `personas/evaluation/`.

| File | Focus |
|------|-------|
| `security.md` | Trust boundaries, attack surfaces, resource bounds in the design |
| `performance.md` | Architectural bottlenecks, coordination points, data structure choices |
| `adversarial.md` | Concrete usage scenarios that lead to bad outcomes |
| `testability.md` | Whether the design is verifiable — observable effects, isolatable components |
| `wildcard.md` | What all the other personas missed |

For the wildcard persona specifically: include the identity statement (first
paragraph) from each of the other personas so the wildcard knows what
territory is already covered.

Before spawning evaluation personas, create a temporary directory for evidence
files (`~/tmp/design-eval-<timestamp>/`). Each persona writes its detailed
analysis to a file in this directory and returns a structured summary to the
orchestrator. The synthesizer works from summaries and digs into evidence
files only when it needs to examine a finding more closely. This prevents
context overload during synthesis.

Evaluation personas identify problems and assess impact — they do not
categorize their own findings as Rejection/Adjustment/Tension. Categorization
is the synthesis step's responsibility.

### Evaluation persona output format

Each evaluation persona produces two artifacts:

**Evidence file** — written to the path provided by the orchestrator. Contains
the full detailed analysis: every finding with complete evidence, full design
element excerpts, detailed reasoning, and complete pass/fail evaluations. This
is the authoritative record.

**Summary** (returned to orchestrator) — a structured summary for the
synthesizer to work from:

**Findings** — ordered by impact (Structural > Significant > Minor). Each:

- **Design element**: The type, boundary, API, or interaction being evaluated
- **Concern**: What the problem is
- **Impact**: Structural (requires rethinking the approach), significant
  (requires notable changes to the candidate), or minor (small adjustment)
- **Evidence**: Brief — full evidence is in the file
- **Suggested change**: If applicable

The impact assessment helps the synthesizer with categorization without
pre-empting it. A persona's "structural" assessment is a strong signal toward
Rejection, but the synthesizer may disagree if it sees the concern addressed
by another persona's suggestion.

**Passes** — things checked that look correct. Brief.

**Uncertainties** — things the persona couldn't determine, and why.

Stage 2 synthesis works from the persona summaries and categorizes each
finding. Provide the paths to each persona's evidence file so the synthesizer
can dig in when it needs more context — when impact assessments conflict, when
a finding's summary is ambiguous, or when it needs to verify the evidence
supports the concern.

Stage 2 synthesis categorizes each finding:

- **Rejection**: A structural problem that invalidates the design direction.
  The candidate cannot be fixed by adjustment — the design personas need to
  rethink the approach. The rejection includes why the direction fails and
  what constraint it violates.
- **Adjustment**: A specific aspect that needs to change, but the overall
  direction is sound. Becomes a constraint for the next design iteration.
- **Tension**: A fundamental conflict that the personas cannot resolve — it
  requires human judgment. Collected and presented at the end.

### The loop

After stage 2 synthesis:

1. If there are only tensions (no rejections or adjustments), the loop
   terminates. Present the design with the tensions for human review.
2. If there are adjustments and/or rejections, feed them back to the design
   personas. Each design persona receives: the prior candidate design, the
   original problem statement, and the categorized findings. Rejections include
   the rationale for why the direction failed — design personas should explore
   a different approach, not patch the rejected one. Adjustments include the
   specific change needed and why — design personas should revise the candidate
   to incorporate them as constraints.
3. The design personas run again with this context, producing a revised
   candidate.
4. Evaluation runs again on the revised candidate. Evaluation personas run with
   fresh context (no knowledge of prior evaluations). The synthesis step
   receives the full history so it can track convergence.
5. Repeat until clean or until convergence failure is detected.

### Convergence failure

The orchestrator monitors the loop for signs that it isn't converging:

- The same evaluation concern keeps appearing across iterations, even after
  design revisions attempt to address it
- Rejections and adjustments are contradicting each other (fixing one
  evaluation concern breaks another)
- The design is growing more complex with each iteration rather than settling

When a convergence failure is detected, the orchestrator stops the loop and
escalates to the human: "Here's the fundamental tension — these concerns pull
in opposite directions, and we need you to decide which matters more." This is
not a failure of the process. Surfacing genuine tensions is one of its primary
outputs.

### Output

The final output includes:

- **Accepted design** (if one emerged): The candidate that passed evaluation,
  with consumer sketches, type definitions, and boundary decisions.
- **Rejected designs**: Each candidate that was rejected during the loop, with
  the rejection rationale. These are valuable — they document explored
  territory and why it didn't work.
- **Unresolved tensions**: Findings categorized as tensions that require human
  judgment.

If the loop terminated via convergence failure rather than a clean evaluation,
there is no accepted design — only the history of attempts, the rejections, and
the tensions.

## Process: lightweight mode

Lightweight mode uses fewer personas and a single pass. It keeps all three
design personas but reduces evaluation to two personas and drops the
feedback loop. Load `/pony-ensemble` for the mechanical process.

### Orchestrator pre-spawn: understand the problem

Same as full mode. Before spawning personas, decompose the problem statement
to the underlying pain point. If the problem statement implies a solution,
peel it back or ask the human. Brief personas with the actual problem.

### Stage 1: Design

Three design personas explore the problem in parallel — the same as full
mode. The same disciplines apply; the decorrelation still comes from
different entry points.

| File | Focus |
|------|-------|
| `consumer-first.md` | Starts from usage code, derives API from what makes call sites clean |
| `skeptic.md` | Questions every abstraction, tries to subtract, proposes the smallest design |
| `principle-checker.md` | Hard verification of each design principle with evidence |

### Orchestrator post-return: evaluate exploration quality

Same as full mode. Evaluate whether personas explored meaningfully different
approaches before forwarding to synthesis. If all three anchored on the same
narrow interpretation, re-brief and re-spawn.

Stage 1 synthesis produces a candidate design using the standard ensemble
synthesis process. The same synthesis guidance as full mode applies:
consumer-first vs skeptic tensions reveal boundaries, principle-checker
violations the others missed are the highest-value findings, and
convergence from different starting points is strong signal.

### Stage 2: Evaluation

Two evaluation personas stress-test the candidate. The adversarial evaluator
always runs. The second slot is context-dependent — if the human specifies
which evaluator to use, use that. Otherwise the orchestrator picks
whichever lens is most relevant to the task:

| When | Pick |
|------|------|
| Design touches trust boundaries or external input | `security.md` |
| Design is on a hot path or introduces coordination points | `performance.md` |
| Design has complex state or will be hard to test in isolation | `testability.md` |

Pick whichever is closest — every design has some risk profile. If
multiple conditions apply, pick the most relevant one. If the reason
for picking a particular evaluator is a characteristic that also
appears in the full-mode selection criteria, that's a signal the task
warrants full mode — don't use the persona pick to compensate for a
wrong mode selection.

Before spawning evaluation personas, create a temporary directory for
evidence files (`~/tmp/design-eval-<timestamp>/`), same as full mode.
Each persona writes its detailed analysis to a file in this directory and
returns a structured summary. Evaluation personas use the same output
format as full mode (evidence file + summary with findings ordered by
impact, passes, uncertainties).

Stage 2 synthesis categorizes each finding as Rejection, Adjustment, or
Tension using the same scheme as full mode.

### No loop — single pass

Lightweight mode does not iterate. After Stage 2 synthesis:

- **Adjustments and tensions**: Present the design with findings to the human.
  Adjustments are expected to be small enough that the orchestrator or human
  can apply them directly. If adjustments collectively amount to redesigning
  rather than tweaking, that's the same escalation signal as high finding
  density — present it to the human.
- **Rejection**: The design direction is wrong. Present the rejected
  candidate, the rejection rationale, and all other findings to the human.
  The human decides what to do — escalate to full mode, fix it directly,
  rethink the problem statement, or something else. Lightweight doesn't
  prescribe the response; it presents the information.

If the review produces an unexpectedly high density of findings relative to
the change size, if a finding reveals the approach is fundamentally wrong,
or if a finding reveals the change touches more subsystems or has more
complex interactions than the mode selection assumed, the orchestrator
presents this to the human. The human decides what to do — the same options
apply.

### Output

The final output includes:

- **Candidate design**: With consumer sketches and type definitions.
- **Adjustments**: Specific changes needed, small enough to apply directly.
- **Tensions**: Conflicts requiring human judgment.
- **Rejection rationale**: If applicable — the structural finding and why
  the design direction was rejected.

## Design values

When principles conflict, these values set the priority. We value the left side over the right — but the right side still matters when the left isn't at stake.

**API safety over API minimality** — an error-prone API should be fixed even if the fix adds surface. Prefer solutions that don't expand the API, but never leave a footgun to preserve minimality.

**Correctness over performance** — never sacrifice correctness for speed. Get it right first, then optimize. A faster wrong answer is still wrong.

**Correctness over concision** — correct but verbose beats concise but wrong. Don't simplify code or APIs at the cost of correct behavior.

**Security over performance** — never skip validation at trust boundaries for speed. Optimize how you validate, not whether you validate. Security is correctness.

**Interface simplicity over implementation simplicity** — accept a harder implementation to give users a clean interface. The consumer's experience matters more than the implementer's convenience.

**Performance over interface simplicity** — runtime speed matters more than programmer convenience. It's acceptable to make things harder on the user to improve performance, but never at the cost of correctness.

**Simplicity over consistency** — don't force artificial consistency when it makes things harder to use. If two similar things genuinely need different interfaces, let them be different.

**Explicitness over implicitness** — when the language allows something to work by magic (implicit conversions, convention-based wiring, unnamed dependencies), prefer the version that states what's happening. The cost of a few extra characters is less than the cost of reconstructing hidden knowledge.

**Type safety over convenience** — use the type system to encode constraints even when it's more work. Distinct types for distinct semantics, validated wrappers over raw primitives, explicit error vocabularies over generic errors. "We could just use a String here" is almost always wrong.

**Changeability over predictive design** — make designs modular and replaceable so future needs can be accommodated, but don't add abstractions, extension points, or features for changes that haven't happened yet. Easy to modify beats designed for a specific predicted modification.

## The disciplines

These are the foundation each persona builds on. Every agent applies all of
them.

### Start from the problem, not the solution

State what problem the user has before proposing any types, traits, or APIs.
"The user needs X" comes before "here's a `SessionStore` trait." If you can't
articulate the problem without referencing your solution, you don't understand
the problem yet.

### Explore before committing

If you only have one idea, you don't have any. The first interpretation of a
problem statement is pattern retrieval — the LLM equivalent of "this looks like
a thing I've seen before." Design starts when you generate a second
interpretation that's genuinely different, not a variation on the first.

Before committing to a direction, explore the design space. Generate multiple
approaches internally — different framings of what the problem is asking for,
not just different implementations of the same framing. Include wild ideas.
They're valuable not because you'll use them, but because they reveal what
matters about the problem. An idea you reject teaches you something about why
you rejected it — that "why" is design knowledge.

Present your best idea, not your first idea. The output is the winner of an
internal competition. The ensemble output format has a "Key decisions:
alternatives considered" section — use it to document what you explored, what
you picked, why, and why you rejected the alternatives. This isn't bookkeeping;
it gives the orchestrator visibility into whether real exploration happened.

The problem statement is where exploration starts, not where it ends. "Add
convenience wrapper methods" is a hint about a pain point, not a design
specification. What pain? Why is the current approach painful? What would
"convenience" actually mean to the user? Different answers to those questions
lead to genuinely different designs — one of which might be "thin wrappers"
and another might be "a unified API that abstracts away the underlying
complexity." Both are valid interpretations of "convenience"; only exploration
reveals which one earns its keep.

### Sketch consumer code first

Before designing any API, write the code that *uses* it. The handler, the
call site, the configuration — the actual application code a user would write.
Not as an afterthought example, but as the first artifact. The consumer sketch
is the specification. It reveals:

- What the API actually needs to provide (and what it doesn't)
- Where type safety breaks down (runtime casts, stringly-typed maps)
- Whether the abstraction can actually serve its purpose (can middleware do
  async work? can the handler access typed data?)
- What the error paths look like from the consumer's perspective

If the consumer code is awkward, the API is wrong. Fix the API, not the
consumer code.

**When claiming consistency between two APIs** (e.g., "guards use the same API
as handlers"), write both consumer sketches side by side. If the method names,
signatures, or interaction patterns differ, the claim is false — address the
discrepancy before proceeding.

### Inventory before inventing

Before proposing a new type, trait, or abstraction, write down what already
exists that addresses the same need: in the codebase, in the language's stdlib,
in the ecosystem. If nothing exists, say so explicitly. If something exists,
start from it — extend, adapt, or compose it rather than building a parallel
structure.

On a greenfield project, "what already exists" means the language's built-in
types, stdlib, and idioms. A new type that duplicates what the language provides
is a smell.

This is not "reuse for reuse's sake." It's a forcing function against the
pattern-matching tendency to invent new abstractions when the problem doesn't
require them.

### Build up incrementally

Don't design the whole thing at once. Start with the smallest coherent piece.
Validate it with a consumer sketch. Then add the next piece and see if it fits.

At each step, ask:
- Does the new piece fit naturally with what's already there?
- Or is it fighting the existing design?
- If it's fighting, is the problem upstream? Would a different foundation make
  this piece fit naturally?

This is how you discover the shape of the problem. A big-bang design papers
over these tensions. Incremental exploration surfaces them while they're cheap
to fix.

### Every step changes what you can see

Every design decision is made with incomplete information. As you explore
further, the territory expands. At step B you could see one option and picked
it. At step D you can see two options that weren't visible from B. Step C might
provide evidence that the option you didn't pick is actually better. None of
this means B was wrong at the time — it means the landscape changed and you need
to look again.

The way you discover this is by constantly pushing on the design: "what if we
did it this other way?" "Does this conform to our principles?" "This doesn't
feel right — why?" These aren't idle questions. They're how you explore more of
the map. Each question might reveal new options, new evidence, or new
connections between decisions you thought were independent.

When the landscape changes, trace back through prior decisions. Not to check
whether they were "disproved" — that's too binary. Check whether the option
space has expanded. Maybe at step B you picked X because it was the only option
you could see. Now at step D you can see X and Y. Which is better given
everything you've learned? Maybe X is still right. Maybe Y is clearly better.
Maybe you need to explore further to tell. All three of those outcomes require
you to actually go back and look rather than assuming B is settled.

This is the core of the design loop. Skipping it is how you end up with designs
that look coherent on the surface but have quiet contradictions baked in — an
app-level-only registration model sitting next to a radix tree that already
knows the route hierarchy, because nobody went back to check whether "app-level
only" still made sense after discovering what the tree could do.

The cost of revisiting decisions is real but bounded. The cost of building on a
decision that should have been revisited compounds with every step forward.

### Question every abstraction

For each type, trait, or interface in your design, ask: is this here because the
problem requires it, or because other systems have it? "Sessions usually have a
SessionStore" is not a reason. "The framework needs to persist session data" is
a reason — but only if the framework actually needs to own that responsibility.

The strongest signal that you're importing rather than discovering: your design
has the same nouns as Rails/Phoenix/Express/Django and you're working in a
language with fundamentally different idioms.

### Name things precisely

Names are the primary interface of a design — they're how it communicates
intent to every future reader. A design that's structurally sound can still
fail in practice because a name suggested something different from what the
thing actually does, and the user built a wrong mental model from it.

This discipline earns its keep at boundaries: public API types, method names,
parameter names, module names — anywhere a user encounters a name and forms an
expectation about what it means. Internal names matter too, but the cost of a
misleading public name is much higher because it shapes how every consumer
understands the system.

At each design step, ask:

- **Does the name come from the problem domain or the solution domain?**
  Problem-domain names ("invoice," "route," "subscription") connect the code
  to what users already understand. Solution-domain names ("manager,"
  "handler," "processor") describe implementation roles that tell the user
  nothing about what the thing actually does. Prefer problem-domain names for
  types the user interacts with; reserve solution-domain names for internal
  machinery where they're the clearest description of the role. Note that some
  of these words become problem-domain vocabulary in specific contexts —
  "handler" is the natural term in web frameworks and event systems. The
  concern is with using them as generic suffixes that avoid naming what the
  thing actually handles or manages.
- **Does the name describe what this thing does, or just what category it
  belongs to?** "Validator" says it validates — but what?
  "InvoiceAmountValidator" says what it validates. "Store" says it stores —
  but a `UserStore` that also sends email notifications lies about its
  responsibilities. A name that categorizes without specifying is a name that
  lets scope creep in without anyone noticing.
- **Could the name mislead a user about what this thing does?** If someone
  reading only the name would form a wrong expectation about the behavior, the
  name is wrong. This includes names that are accurate but incomplete — a
  `Cache` that also writes through to the database is misleading because the
  name suggests read-only caching.
- **Are there names that sound similar but mean different things?** `Session`
  and `SessionState`, `Token` and `TokenData`, `Route` and `Router` — when
  names differ by a suffix or prefix, users will assume the relationship is
  systematic. If `SessionState` is not the state of a `Session`, the naming
  implies a relationship that doesn't exist.
- **Are there names that sound different but mean the same thing?** If the
  design uses `user` in one place and `account` in another for the same
  concept, readers will assume these are different things and spend effort
  trying to understand the distinction. One concept, one name — everywhere.
  This is about vocabulary consistency, not boundary-qualified variants like
  `UserInput` and `UserRecord` — those are distinct types that need distinct
  names per "Distinguish values with distinct semantics."

"Distinguish values with distinct semantics" ensures different concepts get
different types. This discipline ensures those types get names that communicate
what they actually are. A type can be correctly distinct and still misleading
if its name suggests the wrong thing.

When this discipline pushes for more precise names and the skeptic questions
whether the named concepts need to exist at all, surface the tension — both
are needed. Good names make abstractions easier to evaluate: a precisely named
type reveals its purpose, which either justifies or undermines its existence.

### Reason about ownership boundaries

For every capability in the design, ask: does the framework/library own this, or
does the user own this? The answer should come from analysis of the consumer
sketch, not from "frameworks usually own this."

The test: if you removed this from the framework and the user did it themselves,
would anything break? Would anything get worse? If the user can do it better
(more type-safe, more flexible, more natural in the language), the framework
shouldn't own it.

This discipline draws the line between framework and user — the external
boundary. For application-level design where the question is how to organize
*within* the user's code, see "Separate layers."

### Separate layers

"Reason about ownership boundaries" asks whether the framework or the user
should own a capability — the external boundary. This discipline asks the
internal question: within the application, does each piece of logic live in the
right layer?

Layered applications have three layers: domain logic (pure business rules,
zero infrastructure dependencies), orchestration (combines domain logic with
infrastructure — databases, caches, queues), and presentation (adapts
orchestration for a specific protocol — HTTP, GraphQL, CLI). This discipline
operationalizes that separation as design-time questions.

**Scope**: This discipline applies when the skill is used for application-level
design — systems with distinct domain, orchestration, and presentation concerns.
For library or API design where there's no application layering, this discipline
is not relevant. The ownership boundary discipline covers the framework/library
boundary instead. Note that "infrastructure" in the questions below means
infrastructure *relative to the application's domain* — a deployment tool's
domain vocabulary naturally includes container and orchestration concepts, and
"infrastructure" for that tool means the specific database or message queue it
uses to do its work, not the deployment concepts it operates on.

At each design step, ask:

- **Which layer does this belong to?** For every type, function, or interaction
  in the design, classify it: domain, orchestration, or presentation. If you
  can't classify it cleanly, the boundaries are blurred — which usually means
  domain logic has acquired an infrastructure dependency or presentation logic
  has absorbed business rules.
- **Does this domain type depend on any infrastructure?** Domain types should
  have zero infrastructure dependencies — no database clients, no HTTP types, no
  cache interfaces. If a domain type needs to talk to infrastructure, it belongs
  in orchestration, or the domain type needs to express its need through an
  interface that orchestration satisfies.
- **Is orchestration leaking into domain types?** The tell: a domain type that
  knows about connection pools, transaction boundaries, or retry policies.
  Domain logic defines what should happen; orchestration decides how to make it
  happen with real infrastructure.
- **Is domain logic leaking into presentation?** The tell: a request handler
  that contains business rules instead of delegating to orchestration. When
  business logic lives in the presentation layer, it can't be reused by a
  different presentation (a CLI that needs the same logic as the HTTP API).
- **Could you swap the presentation layer without touching domain logic?**
  HTTP → CLI, REST → GraphQL, synchronous → message-queue-driven. If swapping
  the presentation layer requires changes to domain types, those types have
  presentation concerns baked in. This is a thought experiment, not a
  requirement to actually build multiple presentations — it tests whether
  the boundary is clean.
- **Is the presentation layer coupled to orchestration internals?** The tell:
  a request handler that manages transaction boundaries, knows about caching
  strategies, or handles retry logic instead of delegating those concerns to
  orchestration. Presentation should call orchestration and receive results —
  it shouldn't know how orchestration coordinates infrastructure.
- **Are there domain concepts that only exist because of an infrastructure
  choice?** A `PaginatedResult` type in the domain layer exists because the
  database returns paginated results — that's infrastructure leaking into domain
  vocabulary. The domain might need "a bounded subset of results" but shouldn't
  know that the bound comes from database cursor limits.

The test for clean layer separation: can you describe the domain logic without
mentioning any infrastructure technology? If explaining a business rule requires
saying "database," "HTTP," "cache," or "queue," the rule has infrastructure
dependencies that should live in orchestration instead.

"Check cohesion" asks whether things belong together within a type. This
discipline asks a related but distinct question: do things belong together
within a *layer*? A type can be internally cohesive but live in the wrong
layer — a well-structured `UserService` that's cohesive in its
responsibilities but mixes domain rules with database queries. Cohesion
would call it fine (all methods serve "user management"); layer separation
would flag the infrastructure
dependency in domain logic.

"Reason about ownership boundaries" draws the line between framework and user.
This discipline draws lines within the user's code. The two work at different
scales but share a principle: clear boundaries make it obvious where each
concern lives and prevent responsibilities from migrating to the wrong side.

When this discipline pushes toward extracting infrastructure from domain types
and the skeptic questions whether the indirection is worth it, surface the
tension. For small applications or early-stage code, the cost of clean
separation may exceed the benefit — the answer depends on the scale and
expected evolution of the application. But be honest about the tradeoff:
coupling that's cheap
today gets expensive as the application grows, and untangling it later costs
more than separating it now. The skeptic's role here is to prevent ceremony —
extracting an interface that has exactly one implementation and no prospect of a
second is indirection without value. The discipline's role is to prevent
entanglement — domain logic that can't be tested, reused, or understood without
its infrastructure context. When both concerns are real, that's a tension worth
presenting to the human.

### Map state explicitly

State is where most design complexity hides. Boolean flags, nullable fields,
and implicit modes are all state — just state without a name. Unnamed state
can't be reasoned about systematically: you can't enumerate its transitions,
verify its invariants, or ask what happens when an input arrives in a state
you didn't consider.

This discipline earns its keep when a component has multiple interacting pieces
of state, or when state determines which operations are valid. A single flag
that independently tracks one condition doesn't need a state machine — it needs
a good name. For everything else, answer these questions:

- **What states can it be in?** Not just the happy-path states — include
  initialization, error recovery, shutdown, and any transitional states between
  them.
- **What are the transitions?** What event or action moves the system from one
  state to another? Are there transitions the design allows but shouldn't?
- **What invariants hold in each state?** What can the rest of the system
  assume about a component that's in state X? For invariants that span beyond
  individual states — cross-component relationships, ordering constraints — see
  "Articulate invariants."
- **What happens when an input arrives in a state where it doesn't apply?**
  The design should answer this explicitly — ignore, error, queue, crash —
  rather than leaving it undefined.
- **Can the type system encode the states?** If the language supports it
  (union types, sealed classes, enums, trait-based state machines), prefer
  type-level encoding over convention-level tracking. When the type system
  encodes the states, the compiler enforces completeness — every handler must
  account for every state.

The test for whether you've mapped state well: can someone new to the design
draw the state diagram from your description? If not, the state model isn't
explicit enough.

### Articulate invariants

Every design establishes contracts — things that must always be true for the
system to work correctly. Callers rely on ordering guarantees, components depend
on data relationships, operations assume structural properties hold. When these
contracts are implicit, nobody can verify them, nobody knows when they've been
violated, and future changes break them without anyone realizing what happened
until the symptoms surface far from the cause.

State modeling asks "what states can this component be in?" Invariant
articulation asks the broader question: what must always be true across the
entire design? Some invariants are specific to individual states within a single
component (and "Map state explicitly" covers those). But many span the design — relationships between
components, ordering guarantees across sequences of operations, structural
properties that the system maintains by construction or by convention.

At each design step, ask:

- **What can callers rely on?** What guarantees does this API make to its
  consumers? Not just what it returns, but what it promises about the state of
  the system after it returns. If a caller can't answer "what did this operation
  guarantee?" from the API alone, the contract is unstated.
- **What are the pre/post conditions of operations?** What must be true before
  an operation is called, and what does it establish afterward? Preconditions
  that exist but aren't stated become silent failure modes — the operation
  "works" but produces wrong results because the caller didn't know what it
  needed.
- **What relationships between components are maintained by construction vs. by
  convention?** Relationships maintained by construction (enforced by the type
  system, by encapsulation, by the structure of the code) are invariants callers
  can trust without knowing about them. Relationships maintained by convention
  (documented rules, expected call sequences, assumed configurations) are
  invariants that break when someone doesn't read the documentation.
- **Which invariants does the type system enforce, and which depend on correct
  usage?** This is the enforcement boundary. Invariants the type system enforces
  are guarantees. Invariants that depend on correct usage are hopes — they hold
  until someone doesn't know about them. For each convention-dependent invariant,
  ask whether the type system could enforce it instead, and what the cost would
  be.

The test for whether invariants are well-articulated: can a new team member,
reading only the design, list the contracts they must not violate? If any
contract requires reading the implementation to discover, it's implicit.

When this discipline pushes toward articulating more invariants and the skeptic
questions whether those contracts are necessary, surface the tension — both are
needed. The skeptic prevents over-specification (inventing invariants the design
doesn't actually need), while invariant articulation prevents
under-specification (leaving real contracts unstated). The design process should
make the tension visible so it gets an explicit decision.

Note that the skeptic's standard subtraction test — "what breaks if we remove
this?" — is misleading for invariants. Removing an invariant breaks nothing now.
The cost is deferred: it shows up when a future change violates a contract
nobody knew existed. The right skeptic test for invariants is "what does this
prevent?" — not what breaks today, but what incorrect states or sequences does
this contract make impossible.

### Check cohesion

The skeptic asks "should we remove this?" — the subtraction lens. Cohesion is
the complementary grouping lens: do the things that survived subtraction belong
*together*?

A type or module can pass every other discipline and still be a grab-bag of
loosely related functionality. Each piece is justified individually — the
skeptic couldn't remove any of them, the names are precise, the state is mapped,
the invariants are articulated. But the pieces don't cohere. They ended up in
the same type because they were discovered at the same time, or because they
operate on the same data, or because nobody asked whether "same type" was the
right grouping.

The cost of low cohesion is indirect: changes to one responsibility ripple into
code that deals with an unrelated responsibility, because they share a type.
Tests for one responsibility drag in setup for the other. The type's name
becomes either dishonest (describing only one of its jobs) or vague (describing
the grab-bag with a word like "service" or "utils").

At each design step, ask:

- **Does this type have a single coherent purpose?** If you had to describe
  what it does in one sentence without using "and," could you? If "and"
  connects steps in a single workflow or facets of one responsibility
  ("authenticates users and issues tokens"), the type is likely cohesive. If
  "and" connects responsibilities that could each exist independently
  ("authenticates users and sends email notifications"), it's doing more than
  one thing. This isn't about counting methods — a type with many methods can
  be cohesive if they all serve the same purpose.
- **Are there methods or fields that are only used together with a subset of
  the other methods or fields?** If a type has two clusters of functionality
  where each cluster uses its own fields and rarely touches the other's, the
  type is two things wearing a trenchcoat. The clusters should probably be
  separate types.
- **Would a change to one responsibility force changes to unrelated code in
  the same unit?** If modifying how authentication works requires touching
  code that deals with request routing — not because they interact, but because
  they share a type — the grouping is wrong.
- **Did these things end up together for a reason, or by accident?** Common
  accidents: they were discovered at the same time, they operate on the same
  raw data, they're called from the same place, or they were "too small" to
  extract. None of these are reasons for cohesion — they're reasons for
  proximity, which is different.
- **For modules or packages: do the types serve a single coherent theme?** A
  module whose types all participate in one domain concept is cohesive. A
  module that's a drawer for unrelated helpers (`utils`, `common`, `misc`) has
  the same problem at a larger scale — the types don't cohere, they just
  cohabitate.

The test for cohesion: if you split this type along the cluster boundaries,
would either half need to reach back into the other to function? If yes, the
coupling is real and the grouping may be justified. If no, the grouping is
accidental and the type should be split. For data types whose fields represent
attributes of a single domain concept and co-travel through the system,
cohesion comes from domain identity, not field interdependence — the split
test applies to behavioral clusters, not to attribute groupings.

"Distinguish values with distinct semantics" can independently reach the same
conclusion — different responsibilities often mean different semantic
guarantees, which that discipline would flag as needing separate types. When
both disciplines point at the same split, it's a strong signal — but validate
even strong signals against consumer sketches, because two disciplines agreeing
on the wrong split is still the wrong split. When only one does, surface the
tension.

"Name things precisely" often reveals cohesion failures: a type that can't be
named without "and" or that requires a vague name like "context" or "manager"
is usually doing too much. The naming discipline catches the symptom; this
discipline identifies the structural cause.

When this discipline pushes toward splitting a type and the skeptic resists
because each piece is too small to justify its own type, surface the tension.
Small pieces that don't cohere are still better separated — a small focused
type is easier to understand than a large incoherent one. But the skeptic's
resistance may also signal that the pieces genuinely belong together and the
cohesion check is being too aggressive. The design process should make the
tension visible.

### Surface the grain

Every design has directions that are cheap to extend and directions that are
expensive to change. When you decide "variants are types implementing a trait"
or "data flows through a pipeline of transforms" or "each handler owns its own
state," you create a grain. Adding another type to the trait family is with the
grain. Changing the data flow from push to pull is against it. Neither
direction is inherently right — what matters is knowing which is which so the
tradeoff is deliberate.

This is not speculation about future needs. It's understanding the shape of
what you're building now. A design where adding a new output format requires
touching every handler is fine — if the team knows that and decided the
tradeoff was worth it. A design where that same coupling exists but nobody
noticed it is a future surprise.

At each design step, ask:

- **What's easy to add?** If this design needed one more variant, handler, or
  type in the family, where does it slot in? How much existing code needs to
  change to accommodate it? If the answer is "add a new file and implement the
  trait" — that's with the grain. If the answer is "touch five existing types to
  thread the new thing through" — the grain doesn't run that way.
- **What's expensive to change?** If a fundamental assumption changed — data
  flow direction, ownership boundary, concurrency model, storage strategy — how
  much of the design survives? Understanding how deep each assumption is
  embedded lets you make informed decisions about which assumptions to commit to.
- **Does the grain align with the domain's natural variation?** If the design
  makes it cheap to add new data formats but expensive to add new data sources,
  and the domain naturally acquires new sources more often than new formats, the
  grain runs the wrong way.

The consumer-first discipline naturally reveals grain: sketching what "add one
more variant" looks like as consumer code shows whether the grain runs in a
useful direction. If the sketch for a new variant is clean and minimal — just
implement the trait, register it, done — the grain is favorable. If the sketch
requires the consumer to understand and modify internals scattered across the
codebase, it isn't. When applying grain awareness, extend the consumer sketch
beyond just current usage to include at least one "what would adding X look
like?" scenario. Pick the most mundane addition — one more variant of the same
kind the design already handles, not a fundamentally different kind of thing.
If even mundane additions are expensive, the grain is genuinely misaligned. If
only exotic additions are expensive, that's usually the correct tradeoff —
designs can't be cheap in every direction.

The test for whether you've surfaced the grain: can you state, for each major
structural decision, what it makes cheap and what it makes expensive? If you
can't answer that for a decision, you don't yet understand its consequences.

"Check cohesion" asks whether things belong together. This discipline asks what
the grouping makes cheap or expensive. A cohesive type can still have grain
that's misaligned with the domain — the grouping is right, but the extension
point runs in the wrong direction. Conversely, grain analysis might reveal that
a type with good cohesion should be structured differently to align extension
costs with the domain's variation points — which feeds back into whether the
current grouping is actually the right one.

"Map state explicitly" makes grain decisions concrete. A choice between a flat
enum and a trait-based state machine is fundamentally a grain choice: the enum
makes adding transitions cheap (one match in each method) but adding states
expensive (touch every match site); the trait-based machine makes adding states
cheap (new class, implement the trait) but adding transitions expensive (new
method on every state class). Neither is better in the abstract — the right
choice depends on whether the domain's variation is in new states or new
transitions.

When grain analysis and the skeptic point in different directions, surface the
tension — don't silently rework the design. The misalignment may be an
acceptable tradeoff given other constraints. The distinction between the two
lenses: grain awareness observes the structural consequences of decisions
already made; the skeptic guards against acting on predicted needs that haven't
materialized. If the tension forces you to articulate why the grain observation
matters independent of any specific prediction, that's the process working
correctly.

### Look for footguns

After sketching a design, look for ways a user could do something that *looks*
correct but fails silently or in non-obvious ways:

- Can the user set up a configuration that appears valid but doesn't work?
- Can the user call methods in an order that compiles but produces wrong results?
- Are there boolean flag combinations that represent illegal states? If so,
  revisit "Map state explicitly" — the state model is incomplete.
- Does the API make it easy to forget a step?
- Can the user confuse two values that have different semantics but the same type?
  If so, revisit "Distinguish values with distinct semantics" — the type
  boundaries may be too coarse.
- Could a name lead the user to misunderstand what something does and use it
  incorrectly? If so, revisit "Name things precisely" — the name may be
  misleading or too generic.
- Can an operation silently violate an invariant, or does the API rely on an
  ordering guarantee it doesn't enforce? If so, revisit "Articulate invariants"
  — the contract may be unstated.
- Does a type do multiple unrelated things, making it unclear which part of its
  API applies to the user's current need? If so, revisit "Check cohesion" — the
  type may be a grab-bag of responsibilities.
- Is the design expensive to extend in a direction the domain naturally varies?
  If so, revisit "Surface the grain" — the design's cheap-to-extend directions
  may not align with where variation actually occurs.
- Can a domain type only be used when specific infrastructure is available? If
  so, revisit "Separate layers" — domain logic has acquired an infrastructure
  dependency.
- Is any outcome implicit (success by silence, failure by absence)?
- Can the user receive an error and not know what to do with it? If so,
  revisit "Design error vocabularies" — the error types may be too coarse or
  missing context.

The questions above target specific failure modes — things that go wrong. But
a design can also fail by requiring knowledge it doesn't encode. Implicit
mechanisms — setup ordering, required conventions, context-dependent behavior —
create knowledge that exists only in the designer's head. After checking for
concrete footguns, probe for implicit design knowledge:

- What does a user need to know about this design that isn't encoded in the
  types or API?
- Does any behavior depend on context that isn't visible at the call site?
- Are there conventions the user must follow that aren't enforced by the type
  system?
- If a user read only the type signatures (no docs, no examples), what would
  they get wrong?

The last question is a forcing function — it surfaces every piece of implicit
knowledge the design depends on. Each answer is either an acceptable
documentation requirement or a design problem to fix. If the list is long, the
design is too implicit.

A candy-machine interface is one where the user can put the money in the slot
and push the button and get something other than what they expected. Good design
makes the right thing easy and the wrong thing impossible (or at least loud).

### Distinguish values with distinct semantics

Two values that look similar but carry different guarantees, different lifetimes,
or different validation states are not the same thing. Sharing a type between
them forces callers to use out-of-band knowledge to tell them apart — which
guarantee does this `String` carry? Is this `User` from input or from the
database? Did this `Config` pass validation?

This discipline is an active counterbalance to subtraction. The skeptic asks
"what breaks if we remove this type?" and the answer may be "nothing breaks
right now." But that's the wrong test when two values have different semantics.
The right test is: can a caller distinguish them without context they shouldn't
need? If collapsing two types into one means the caller must remember which kind
they're holding, the types should stay separate — even if the fields are
identical today.

At each design step, ask:

- Do any values in this design have different meanings but share a
  representation?
- If two things look similar, do they carry different guarantees, different
  lifetimes, or different validation states?
- Would collapsing two types into one force callers to use out-of-band knowledge
  to distinguish them?
- At each data boundary (input, storage, output, inter-component), is the type
  actually the same concept or a similar-looking different concept?

When this discipline and the skeptic's subtraction pull in opposite directions,
that's a tension worth surfacing — not a conflict to resolve silently. Both are
needed: subtraction prevents unnecessary abstraction, distinct-semantics prevents
premature unification. The design process should make the tension visible so it
gets an explicit decision.

### Design error vocabularies

Error types are not just return values — they're an API. "Distinguish values
with distinct semantics" asks the general question: do any values in this design
have different meanings but share a representation? This discipline applies that
question specifically to error types, where the consequences of getting it wrong
are distinct: a caller that can't tell errors apart can't handle them correctly,
and context lost at a wrapping boundary is gone forever.

At each layer or boundary in the design:

- **What are the distinct failure modes?** Enumerate them. If two failure modes
  need different handling by the caller, they need different representations. If
  two failure modes always get the same treatment, they might be one.
- **Does each error carry enough context for the caller to act?** "Not found" is
  reporting. "Not found: key X in store Y" is actionable. If the caller needs to
  do something about the error — retry, fall back, present a specific message —
  it needs the data to do so.
- **Are distinct failures collapsed into one type?** A generic "parse error" that
  covers both "malformed input" and "unsupported version" forces the caller to
  guess which it is. This is the error-specific form of premature unification.
- **How does context propagate across layers?** When a low-level error gets
  wrapped by a higher-level one, is the original context preserved? Can a human
  (or a log aggregator) trace the error back to its source? Information lost at
  wrapping boundaries is gone forever.
- **Can the consumer distinguish errors that need different handling?** The
  consumer sketch shows what the match statement looks like. The question here is
  whether the error types *support* the distinctions the consumer needs. If the
  consumer has to inspect string messages or use out-of-band knowledge to tell
  errors apart, the vocabulary is too coarse.

The consumer-first discipline sketches what error handling looks like from
outside — it reveals what distinctions the caller needs. This discipline designs
the error types themselves, ensuring they carry the right distinctions and enough
context. Both are needed: the consumer sketch is the specification, this
discipline is the implementation check.

When this discipline pushes toward more error variants and the skeptic's
subtraction pushes toward fewer, surface the tension — don't resolve it silently.
Each error variant added to a public API is hard to remove later; the consumer
sketch shows which distinctions the caller actually needs versus which are
internal detail.

### When in doubt, ask

Design is full of decision points where two reasonable paths diverge. When you
hit one — when a design choice could go either way and you don't have a clear
reason to prefer one — stop and ask. Present the tradeoff, say what you're
uncertain about, and get input before committing to a direction.

The instinct to keep moving and produce a complete design is the enemy here.
An unasked question that leads to a wrong turn costs more than the pause. The
whole point of collaboration is that the human has context and judgment that
the model doesn't. Use it.

This applies especially to:
- Ownership boundaries (should the framework own this or the user?)
- Abstraction level (is this too much? too little?)
- When the consumer sketch reveals a tension and you're not sure which side to
  resolve it on
- When you're about to add something because other systems have it but you're
  not sure this system needs it

### Design is the map, the plan is one path

Design explores the territory — the full space of what could exist, how pieces
relate, where the constraints are. A plan picks one path through explored
territory to implement within a specific scope. The map doesn't stop being
useful once you pick a path. Keep mapping while you walk, because what you learn
during implementation changes your understanding of the territory.

Design insights that go beyond the current plan's scope are still valuable. They
inform constraints on what you build now (don't build something incompatible
with where you're headed) and get recorded (discussions, issues, plan notes) so
future work can use them. "This is the right design" and "we implement all of it
now" are separate decisions.

The disciplines in this skill — consumer sketches, abstraction questioning,
footgun scanning — are not a checklist you run once during a "design phase."
They're lenses you keep applying. Every time the design changes, run them again
on the changed parts and on the parts that depend on what changed. A discipline
that only runs once is a ritual, not a practice.

## Anti-patterns

These are the specific failure modes this skill exists to prevent. If you catch
yourself doing any of these, stop and reorient.

**Designing the complete system at once.** If your first artifact is a full
design document with all types, all interactions, all edge cases — you skipped
the discovery process. Back up. What's the smallest piece?

**Starting from solution shape instead of problem statement.** If your design
document opens with type definitions rather than "the user needs to..." — you're
retrieving, not designing.

**Committing to the first interpretation.** When the problem statement implies an
approach ("add convenience wrapper methods"), treating that as the design rather
than as a hint about a pain point. If every persona produced the same kind of
solution, nobody explored — they all pattern-matched on the problem statement and
dressed up the first idea. The tell: the "alternatives considered" section is
empty or lists only variations on the same approach, not genuinely different
framings of what the problem is asking for.

**Importing patterns without questioning fit.** String-keyed maps, middleware
chains, context objects, store traits — these exist in many frameworks. Their
presence elsewhere is not evidence that your system needs them. Evaluate each
one against the actual consumer code.

**Consumer code as an afterthought.** If the example usage appears at the end of
the design document (or not at all), the API was designed without its primary
constraint. Move the consumer code to the beginning.

**Giving the framework too much responsibility.** When in doubt, the user owns
it. The framework can always take on more responsibility later; taking it back
is a breaking change.

**Claiming consistency without verifying it.** "This uses the same API as X"
is a testable claim. Write both usages side by side. If they don't match, the
design has a problem — either make them actually match or drop the claim and
design each on its own merits.

**Naming from the solution domain instead of the problem domain.** If you
can't explain what a type does without restating its name — "it manages
connections," "it handles requests," "it processes events" — the name is a
solution-domain label, not a problem-domain description. The tell is that the
name describes the type's role in the code structure rather than what it means
to the user. A `ConnectionManager` might be fine as an internal implementation
detail, but if it's in the public API, the user has to open the docs to find
out what it manages and how.

**Inventing when extending would suffice.** Proposing a new type when the
codebase, language, or stdlib already has something that serves the same
purpose. The new type may feel cleaner in isolation but adds a concept the user
must learn and the codebase must maintain.

**Collapsing distinct semantics into a shared type.** Using one type for two
values that carry different guarantees — user input and a validated record, a
database row and an API response, a request and a stored entity. The fields may
look identical, but the values mean different things at different boundaries. The
skeptic's "what breaks if we remove this?" may not catch it because nothing
breaks structurally — the breakage is semantic, showing up as a caller that
treats an unvalidated input as a trusted record or vice versa.

**Treating error types as an afterthought.** Designing the happy-path types and
interactions first, then bolting on generic error types at the end. Error
vocabularies designed this way tend to be too coarse — one error type for many
distinct failure modes — because they weren't part of the design exploration.
Error types should emerge alongside the domain types; they're part of the API,
not an appendage.

**Skipping evaluation.** Producing a design from the design personas and going
straight to implementation without running the evaluation stage. The evaluation
personas catch structural problems — security gaps, performance ceilings,
untestable interfaces, adversarial usage scenarios — that the design personas
aren't looking for.

**Representing state implicitly through field combinations.** When multiple
fields interact — boolean flags, optional fields, status enums paired with
counters — the component has an implicit state machine. Boolean flags are the
most common form: n interacting flags create 2^n combinations, most invalid
(authenticated-but-not-connected is probably illegal). But any set of fields
whose valid combinations are a proper subset of all possible combinations has
the same problem: no transitions, no invariants, no handling for illegal
combinations. Name the states instead: the valid combinations are the actual
states, and making them explicit lets the type system enforce which transitions
are legal.

**Leaving invariants implicit.** When a design establishes contracts between
components — ordering requirements, data relationships, structural properties —
but never states them. The contracts exist whether or not they're documented:
callers depend on them, implementations preserve them, and future changes break
them. The difference between a stated invariant and an unstated one is that
when the stated one breaks, you know what went wrong and why. When the unstated
one breaks, you get symptoms far from the cause and no trail to follow.

**Committing to structure without understanding its grain.** Making structural
decisions — "variants are enum cases," "handlers are registered at startup,"
"data flows through a transform pipeline" — without asking what those decisions
make cheap and what they make expensive. Every structural choice creates a
grain; ignoring the grain means discovering the tradeoff only when you need to
go against it, at which point the cost is high and the decision is baked in.
The result is designs where the expensive direction turns out to be the one the
domain actually needs, and nobody knew until the first extension attempt.

**Embedding infrastructure in domain types.** When a domain type directly uses
database clients, HTTP types, cache interfaces, or other infrastructure. The
domain type might be correct about the business logic, but it can't be tested
without the infrastructure, can't be reused in a different deployment context,
and can't survive an infrastructure swap. This is distinct from "accumulating
unrelated responsibilities" — the type may be cohesive in purpose but coupled to
the wrong layer.

**Accumulating unrelated responsibilities in a type.** When a type grows by
accretion — each new responsibility is too small to extract on its own, so it
gets added to the nearest existing type. The result is a type that does five
things, none of which is its primary purpose, because no single addition was
large enough to trigger extraction. The tell: methods or fields that cluster
into subsets that don't interact with each other, or a type whose name has
drifted to something vague ("manager," "context," "helper") because no precise
name can describe everything it does. Unlike "collapsing distinct semantics,"
which is about *values* sharing a type they shouldn't, this is about
*responsibilities* sharing a type they shouldn't.

## Pony-specific design guidance

When designing Pony APIs, libraries, or framework features:

- **Leverage the type system.** Union types for state instead of boolean flags.
  Distinct types for distinct semantics. `Any val` is almost always a sign that
  the design is avoiding a harder type-safety question — answer that question
  instead.
- **Make illegal states unrepresentable.** Pony's type system is strong enough
  to encode most constraints. If a combination of values is illegal, the types
  should prevent it from existing.
- **Be skeptical of patterns from dynamic-language frameworks.** Middleware
  chains, string-keyed context maps, convention-over-configuration — these
  patterns compensate for weak type systems. Pony has a strong type system. Use
  it. The idiomatic solution in Pony often looks nothing like the idiomatic
  solution in Ruby or Python.
- **Favor trait-based state machines for stateful components.** When a
  component has distinct phases where valid operations change between them,
  represent each phase as a separate type implementing a shared interface
  rather than using flags or optional fields. The actor becomes a thin shell
  that delegates to the current state object — state transitions replace
  the object, and the old state's resources are released automatically. See
  the state machine pattern in `/pony-ref`. Marker primitives with scattered
  `match _state` / `if _state is` checks are a step above boolean flags but
  still fragment behavior across the actor's methods — use them only for
  simple guards within a single behavior, not for routing different behavior
  across multiple events. The test: if more than one behavior needs to check
  the state to decide what to do, the actor needs a trait-based state machine.
- **Think about capabilities.** Who can read this? Who can write it? Who can
  send it across actor boundaries? If the design requires `val` but the consumer
  naturally produces `ref`, there's a friction point worth examining.
- **Understand what composition looks like in the specific context.** Don't
  assume a single composition pattern. In a web framework with actor-per-request,
  the handler actor might be the composition unit. In a parsing library, it
  might be function composition. In a template engine, it might be class
  hierarchies. Let the problem dictate the composition model.
