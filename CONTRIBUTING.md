# Contributing

It's good to hear that you want to contribute to Pony LLM Skills!

There are a number of ways to contribute. As this document is a little long, feel free to jump to the section that applies to you currently:

* [Discussions and issues](#discussions-and-issues)
* [Bug report](#bug-report)
* [Improving an existing skill](#improving-an-existing-skill)
* [Proposing a new skill](#proposing-a-new-skill)
* [How to contribute](#how-to-contribute)
* [Pull request](#pull-request)

## Discussions and issues

We use [GitHub Discussions](https://github.com/ponylang/llm-skills/discussions) as the starting point for most conversations — questions, ideas, feedback, and new skill proposals all belong there. Issues are reserved for actionable work items: confirmed bugs and tasks that someone is going to fix. If you're not sure whether something is a bug, start with a discussion and it can graduate to an issue once the problem is understood.

## Bug report

First of all please [search existing issues](https://github.com/ponylang/llm-skills/issues) to make sure your issue hasn't already been reported. If you cannot find a suitable issue — [create a new one](https://github.com/ponylang/llm-skills/issues/new).

For bugs in `install.py`, include:

* what you ran,
* expected result,
* actual result, and
* your Python version and operating system.

For problems with a skill (incorrect guidance, outdated information, confusing wording), describe what the skill told you and what the correct behavior should be.

## Improving an existing skill

Improvements to existing skills are always welcome. This includes fixing inaccuracies, clarifying wording, adding coverage for missing topics, and updating content that has gone stale. Please open a discussion in the [Skill Improvement](https://github.com/ponylang/llm-skills/discussions/categories/skill-improvement) category first to describe what you'd like to change and why. Once there's agreement, it can move to a PR.

## Proposing a new skill

If you'd like to add a new skill, please open a discussion in the [New Skill](https://github.com/ponylang/llm-skills/discussions/categories/new-skill) category before putting in the work. A proposal should cover:

* what problem the skill addresses,
* who the intended audience is (Pony developers, general LLM users, etc.), and
* why it doesn't fit into an existing skill.

This helps avoid duplicate effort and ensures the skill fits the project's direction. Once there's agreement on the proposal, it can move to a PR.

## How to contribute

We use a fairly standard GitHub pull request workflow. If you have already contributed to a project via GitHub pull request, you can skip this section and proceed to the [specific details of what we ask for in a pull request](#pull-request). If this is your first time contributing to a project via GitHub, read on.

Here is the basic GitHub workflow:

1. Fork the llm-skills repo. You can do this via the GitHub website. This will result in you having your own copy of the llm-skills repo under your GitHub account.
2. Clone your llm-skills repo to your local machine.
3. Make a branch for your change.
4. Make your change on that branch.
5. Push your change to your repo.
6. Use the GitHub UI to open a PR.

Some things to note that aren't immediately obvious to folks just starting out:

1. Your fork doesn't automatically stay up to date with changes in the main repo.
2. Any changes you make on your branch that you used for the PR will automatically appear in the PR so if you have more than 1 PR, be sure to always create different branches for them.
3. Weird things happen with commit history if you don't create your PR branches off of main so always make sure you have the main branch checked out before creating a branch for a PR.

If you feel overwhelmed at any point, don't worry, it can be a lot to learn when you get started. Feel free to reach out via [Zulip](https://ponylang.zulipchat.com/#narrow/stream/192795-contribute-to-Pony).

You can get help using GitHub via [the official documentation](https://help.github.com/). Some highlights include:

* [Fork A Repo](https://help.github.com/articles/fork-a-repo/)
* [Creating a pull request](https://help.github.com/articles/creating-a-pull-request/)
* [Syncing a fork](https://help.github.com/articles/syncing-a-fork/)

## Pull request

While we don't require that your pull request be a single commit, note that we will end up squashing all your commits into a single commit when we merge. While your PR is in review, we may ask for additional changes, please do not squash those commits while the review is underway. We ask that you not squash while a review is underway as it can make it hard to follow what is going on.

When opening your pull request, please make sure that the initial comment on the PR is the commit message we should use when we merge. Making sure your commit message conforms to these guidelines for [writ(ing) a good commit message](http://chris.beams.io/posts/git-commit/).

Make sure to issue 1 pull request per feature. Don't lump unrelated changes together. If you find yourself using the word "and" in your commit comment, you are probably doing too much for a single PR.

Pull requests from accounts that aren't members of the Ponylang organization require approval from a member before CI will run. Approval is required after each update that you make. If you are opening PRs to verify that changes pass CI before "opening it for real", we strongly suggest that you open the PR against the `main` branch of your fork. CI will then run in your fork and you don't need to wait for approval from a Ponylang member.

## Skill structure

Each skill is a directory at the repository root containing at minimum a `SKILL.md` file. This is the file that LLM harnesses load when the skill is invoked.

Skills may also include:

* A `personas/` subdirectory for ensemble-based skills that use multiple agent personas.
* A `references/` subdirectory for supplementary reference material that the skill loads on demand.

When adding or modifying skills, make sure to update the `README.md` to reflect the changes — including the skill description, what's in the quick reference, and the suggested trigger if applicable.

## Documentation formatting

When contributing to documentation, try to keep the following style guidelines in mind:

* Wherever possible, try to match the style of surrounding documentation.
* Avoid hard-wrapping lines within paragraphs (using line breaks in the middle of or between sentences to make lines shorter than a certain length). Instead, turn on soft-wrapping in your editor and expect the documentation renderer to let the text flow to the width of the container.
