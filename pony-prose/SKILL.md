---
name: pony-prose
description: How the words go in a comment, docstring, release note, README, or a project's AGENTS.md — write plainly, say the fact, and stop. Load before writing any prose that ships with the code. Language-agnostic.
disable-model-invocation: false
---

# Prose

The form tells you what to say. This tells you how to say it.

A comment, a docstring, a release note, a CHANGELOG entry, a README, a project's `AGENTS.md`, an issue body, a PR description, a commit message — each has a skill that says what belongs in it and what to leave out. This skill is the layer under all of them: how the words themselves read once you've decided what to write. Load it alongside the form's own skill.

## Plain is where you stop

Get the true thing down with no decoration, and that is the finished state. There is no later pass that adds flourish on top. A blog post earns its flourish; a docstring does not. For the forms this skill governs, plain is the finished state, not a step toward something more polished.

Short, direct sentences. State each fact as plainly as you can. If a reader would have to reread a sentence to work out what it means, it is too clever or too packed; say the thing first, in plain words, then the mechanism.

## Say the fact

Every sentence has to carry something a reader could check or act on: what changed, what broke, what it does now, the actual mechanism named plainly.

The check is mechanical. Cover the decorative part of a sentence and read what is left. If a concrete claim remains, keep it and cut the decoration. If nothing is left, the sentence is empty — it sounds like something and says nothing — so write the real fact in or cut the sentence. "Small buffers were reallocating when they had no business doing so" — "no business" is an opinion, not a fact; say the change: building a small buffer no longer does an extra reallocation.

## Don't reach for phrasing instead of the fact

Flourish that stands in for content is the most common failure and the hardest to catch, because it reads well. It takes six forms:

- **Flowery language** — purple prose, excess adjectives, ornament for its own sake.
- **Mannered, essayistic register** — "at the center of the answer is," "X answers Y's question." Write directly instead.
- **Contrived parallels reached for rhythm** — "same input, same code, three different answers." Cover the parallel; if the plain fact remains, the structure was decoration.
- **Mathematical-symmetry framings** — "the dual of," "the inverse of," "isomorphic to" for "the opposite of." Say it does the reverse, plainly.
- **Definitional label-parallels** — "X is the A, Y the B," balanced clauses that say what things are and nothing about why they matter. Say what the thing does.
- **Generic AI tells** — "it's worth noting that," "importantly," "interestingly," overly balanced hedging, and em-dashes on every other line. Cut them.

All six are the same move: you reached for how it sounds instead of stating what is true. Cover the phrasing; if a fact is left, keep it; if not, write the fact in.

## Cut formulaic docstring openers

"Names the current stdin subscription." "Represents the retry budget." "Holds the parsed header." "This method returns the count." Each describes the field or the method instead of the thing itself. Cover the opener — "Names the," "Represents the," "Holds the," "Stores the," "This method" — and read what is left: if a plain description of the thing remains, the opener was carrying nothing; if nothing remains, you described the code element and never said what the thing is. Write what it is or does: "The current stdin subscription." "Returns the number of active connections."

## Never coin jargon

Prose exists to explain. Never name what the code does in shorthand you minted on the spot: invented compounds ("green-skip," "main miss"), pseudo-technical labels. The tell is that the term reads like real vocabulary — next to "garbage collection" it looks legitimate — but nobody can decode it, because it means something mundane. Write what happens in plain words. Established domain terms, and terms the project itself defines, are fine.

## Nothing that isn't a person acts

Don't give a non-person noun knowledge, intent, sight, or a job. This is not only about code — run the check on every noun: a bug, a test, the data, the layout, the runtime, a release, a version, a change.

Replace cognition and intent verbs (asks, answers, wants, knows, decides, tries, sees, watches, catches, "its job is to") with what the thing mechanically does (runs, compares, returns, finds, walks, computes, records). "The check asks whether the value is valid" → "the check compares the value against the bound." "The test catches the bug" → "the test fails when the value is wrong." A second class is static things given an action they can't take: a library, a release, a version, a change don't act at all. "The libraries picked up the change" → "we shipped new versions." The action belongs to a person or to a machine's literal operation; put it there.

## The reader has only what you gave them

Every "it," "this," "that" needs an obvious referent. If the antecedent isn't in the same or the previous sentence, name the thing. Unclear antecedents are a failure of craft, not a stylistic preference.

Introduce a concept before you rely on it, and introduce it before you name it — the idea first, the label second. A term named once in a compressed clause is not taught. The same holds for capacious words ("the work," "tooling," "scale," "the problem"): anchor them to something concrete before you build on them, or the point that depends on them won't land.

## Don't inflate, don't invent

State what is true, and don't reach past it. Plain writing fails this way too — not by adding flourish, but by inflating the fact itself to sound more impressive.

Don't write that something is "impossible" or "can't happen" when it is possible and only non-obvious. The honest word is "surprising" or "non-obvious," not "impossible" — and claiming a system does the impossible reads as not understanding it.

Every claim about history, severity, size, or frequency is a factual claim. Verify it from the source or drop it. Don't invent specifics to fill a plausible-sounding sentence. And don't editorialize about what the reader knows — "obvious," "as everyone knows," "counterintuitive" all presume the reader's state; present the fact and let them react.

## Don't pre-announce the shape of an explanation

"The intuition, in two lines." "Both rules in one sentence." "How it works, in three steps." Just deliver the explanation. The reader can see the shape; the announcement is filler.

## Aim at the problem, never the person

When the prose is about someone else's code, PR, design, or decision — a bug report, a commit message, a release note, a review comment — aim every criticism at the problem, never at the person or their competence. The failure mode is subtle: quoting a stated goal and then declaring it false, a "why did nobody catch this" angle that lands as negligence, a closing jab at the work. Each reads as an exposé of the author even when that wasn't the intent. Credit what works, locate the cause in a structural reason (a subtle interaction, a pre-existing constraint) rather than in someone's carelessness, and stay direct about the problem while generous about the people.

The same fact can be aimed at the problem or at the person. Which one you pick is how you say it — so it belongs here.

## Where this sits

This skill owns how the words read. It owns nothing about what to say or what to leave out — that is the form's job. `pony-comments` says what earns a comment; `pony-release-notes` says what belongs in a release note; the README skills say what a README holds; `pony-agents-md` says what earns a line in a project's `AGENTS.md`. Load the form's skill for what to write, and this one for how to write it.
