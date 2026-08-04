---
name: pony-agents-md
description: What belongs in a project's AGENTS.md and what never does. Load before writing or changing AGENTS.md or CLAUDE.md. Language-agnostic.
disable-model-invocation: false
---

# AGENTS.md

Every line in a project's `AGENTS.md` is paid for on every task in the repository, forever. No other prose the project has is read this often, by this many readers, none of whom asked for it. It is the most expensive writing in the repo per word, and the cost is invisible to the agent adding to it.

Where a project keeps this content in `CLAUDE.md` instead, it is the same file under another name, and everything here applies to it.

Load `pony-prose` first: it is the rulebook for how the words read. This skill is the rulebook for what earns a line.

## The principle

An agent lands here cold, with no memory of the last one. `AGENTS.md` exists to save it the cost of learning, again, what it cannot learn cheaply from the repository itself.

> A line earns its place only if reading it here is cheaper and truer than how an agent would otherwise learn the same thing.

Both halves matter, and the second is the one that gets lost. The code cannot drift from itself. A sentence here about the code is a second copy that no compiler checks and no test covers, so it starts out less true than the thing it describes and gets worse from there. To beat that, a line has to be *much* cheaper to read here, not marginally.

Almost nothing about the code is.

## The check

Applying the principle line by line is slow. This is the fast version for a fact about the code, and it usually gives the same answer:

> Name the one thing in the code this fact is about — a type, a function, a file.

If you can name it, cut the line. An agent that needs the fact will be reading the thing the fact is about, and will find it there. The copy here is paid for by every agent that never looks.

If you cannot name one thing — if the fact is about how the pieces relate, what shape they make, which idea the design turns on — then nothing owns it, no single file can hold it, and assembling it means reading the whole package. That is expensive, and this is its only home.

The check is for facts about the code, because that is what this file fills up with. The commands, the conventions, and the traps below are not facts about the code, and it does not reach them.

### When the check and the principle give different answers, the principle wins

A fact about the code can have an owner and still earn its place, when the shape it belongs to cannot be recovered cheaply from that owner.

A connection lifecycle is the case. Its state classes all live in one file, so the check names that file and evicts. But the shape is not written down anywhere in it: an agent has to know the lifecycle exists, know to go there, and read the file end to end to assemble the transitions out of the classes. Reading it out is expensive, so the principle says keep it and the check yields.

The exception buys you one picture, of the package as a whole. It does not buy you a tour. Draw the lifecycle; do not tabulate what each state returns — the states hold that, and an agent reading a state has it. The moment you are covering subsystems one at a time, you have stopped drawing a picture and started transcribing the code, and no number of invocations of this exception makes that a picture.

## The cut line usually goes nowhere

The code already says it. That is *why* you could name the owner.

Do not soften a deletion by moving the prose into a docstring. A docstring gives a caller what they need to use the thing correctly and says nothing about how it works — that is `pony-comments`, and a state table, a call sequence, or a restated signature breaks that rule on arrival. Moving such prose next to the code does not make it any more true; it only makes it harder to spot. Write a docstring when a caller needs one, on its own merits, under its own rulebook.

## Never describe the current code

The sentence you most want to write is the one that cost you the most to learn, and it is almost always a description of a body that someone is about to rewrite. Apply the check from `pony-comments` — the same rot, a different file:

> If rewriting a body, without changing anything a caller relies on, would make this sentence false, it describes how the code works now. It does not belong here.

A state table. A field list. A call sequence. A restated signature. An enumeration of callbacks. Each is a claim about the present tense of a body that will be rewritten.

The picture is not an exception to this rule; it passes it. That `pony-comments` check is scoped to a body, and you can rewrite every method in a state class without changing the states or the transitions between them, so the picture survives. When a change really does alter the shape, the picture is *supposed* to change with it. That is not rot. That is the sentence being true.

## What earns a line

**The picture.** What the pieces are, how they relate, which idea the design turns on. No docstring can hold it, and it is what lets a cold agent start in the right place instead of reading three thousand lines to find out where that is. It is short.

**The commands.** Build, test, run a single test. Especially the ones that fail if you guess them — a required flag, a target that is not the obvious one. An agent cannot derive these.

**The conventions.** Rules an agent will otherwise break. Each reads as an instruction it could disobey: *dispose every actor a test listener creates, or the runtime will not exit and CI hangs.* If it does not read as an instruction, it is a description, and the rule above applies to it.

**The traps.** A thing that was tried, shipped as a bug, and must not come back. Three parts: what you would naturally do, what happened when someone did, and don't. Name the pull request or the issue.

The trap is the one thing here that the code cannot give you. The code records what is. Nothing in it records what was tried and rejected — so a plausible wrong idea, already had once and paid for once, will be had again by the next agent, and the one after that. This is the section that justifies the file existing.

## Never

**A source-tree listing.** `ls` is cheaper and it is never out of date.

**A tutorial.** That is `examples/`, and the examples compile.

**An API guide.** That is the package docstring, and it renders into the generated documentation.

**A history.** Version control remembers. A trap is not a history — it is a live constraint that happens to carry a date.

## When it is wrong, delete it

An agent reports that `AGENTS.md` is out of date. The default is to delete the section, not to update it.

If it describes the code and the code moved, it should never have been here. Updating leaves the same section in place for the next agent, longer and bound more tightly to the code than before — so it goes false again, sooner. Every staleness report answered with an edit makes the next one more likely.

Update only what was meant to be here: a command, a convention, a trap, or a picture whose shape actually changed.

A file that keeps going out of date is not under-maintained. It is describing something it was never supposed to describe.

## Don't review your own addition

You are the worst-placed agent in the project to judge what belongs here. You have just done the work. Every detail is loaded, every one was expensive, and all of it feels necessary. The agent this file is written for arrives knowing none of it — and that agent is the only one whose judgment counts, because it is the reader.

So don't judge. Spawn the reader — use `claude-opus-4-6` if the session uses an Anthropic model, otherwise your most capable available model.

Do this for a new section, a rewrite, or anything you would have to argue for. A one-line command fix does not need it.

Give a fresh-context subagent two things: the repository, and the proposed `AGENTS.md` in full. Tell it not to read the diff, the branch, the git history, the pull request, or the issue. It has the repository, so it *can* reconstruct all of them, and the withholding only holds if you ask for it. If your harness loads `AGENTS.md` or `CLAUDE.md` into every agent it spawns, move the file out of the tree for the run — otherwise the reader is holding the thing you meant to withhold, and it will tell you what you want to hear.

Its ignorance is not a limitation to design around. It is the reader's condition, and it is the only vantage from which the questions can be answered.

Ask it two:

1. **Take each section, and name the one thing in the code it is about.** Cut what it can name, unless the section draws a shape that cannot be recovered cheaply from the thing that owns it.

2. **For what survives — is reading it here cheaper and truer than reading the code?** Make it defend each one. That a line is true, and that it is useful, is not the bar. The bar is that carrying it on every task, forever, beats the alternative way of learning it.

It judges the whole file, not your change, so it will raise findings against sections you did not touch. Those don't block you. Before you set one aside, ask whether it means your change was scoped too small — the cleanup you are doing may be the place it belongs. What survives that question, capture and vet afterwards; `pony-vet-suspected-issues` has the procedure.

Findings against what you added do block you. If you disagree with one, that is a question for a human, not a thing to overrule. You are the party with the conflict of interest.

## Calibration

The reader above tells you what to cut. It cannot tell you what is missing: it has read the file and the code, but it has not tried to *do* anything, so it has fumbled nothing.

For that, run a cold agent on real work, once in a while. Hand it an ordinary task in the repository with `AGENTS.md` withheld, and watch: what it searches for twice, what it gets wrong, what it has to be told. That is what belongs in the file. Everything else in there is something you are paying for and nobody needed.
