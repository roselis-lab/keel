# Keel

**A GenAI threat catalog your security team keeps in its own Git, and an agent workflow that assesses one of your AI systems against it and hands back a report.**

[![CI](https://github.com/roselis-lab/keel/actions/workflows/ci.yml/badge.svg)](https://github.com/roselis-lab/keel/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Keel runs inside the coding agent your engineers already use: Claude Code, Codex, Cursor, GitHub Copilot, OpenCode, Kilo Code or Gemini CLI. You describe an AI system. The agent checks it against the catalog, asks you when a fact is missing, rules out what cannot happen in that system with the reason written down, and saves a report your team reviews, signs off and publishes.

## What your team gets

- **A threat catalog you own.** GenAI threats and the controls against them, as YAML files in your repository. A change to the catalog is a pull request: reviewed like code, checked by CI.
- **Assessments that show their reasoning.** A report lists the threats that apply to the system with severity and likelihood, the threats ruled out and why, and the controls still to build.
- **A history per system.** One report per system per date. A re-assessment starts from the last report and states what changed.
- **A read-only site for everyone else.** `keel site` turns the catalog and the signed-off reports into plain HTML pages. GitHub Pages or GitLab Pages publishes them, behind the access control your Git host already has.
- **A map to the lists auditors ask about.** Every entry of the OWASP Top 10 for LLM Applications 2025, the OWASP Top 10 for Agentic Applications 2026, MITRE ATLAS 5.6.0 and the Google SAIF risk map has a row: covered, out of scope with the reason, or an open gap.

## A first assessment, end to end

Take the demo system in [`docs/demo/system-under-assessment.md`](docs/demo/system-under-assessment.md). It is made up: "Halo", a support assistant inside a web app. It can look up orders, issue refunds up to $500, change shipping addresses and escalate to a person. It searches the help centre, customers' past tickets and internal runbooks, and keeps a short note about each customer.

You open your copy of Keel in your agent, paste that description and ask: *"Assess the GenAI security of this system."* The agent then:

1. checks whether this system has been assessed before, and if so, works from the last report;
2. picks the catalog threats that could fit, and tests each one's "does not apply when" condition against Halo. One that stays live: the chat panel renders the model's markdown, images included, so a model-supplied image URL is a request the user's browser makes;
3. stops and asks whenever it needs a fact the description does not give, instead of guessing either way;
4. saves a draft report to `reports/<system-id>/<date>.yaml` and gives you a link to it.

You open the draft in the local UI (`uv run keel up`), correct grades and wording, and mark it final.

**Who you need.** Someone who knows the system's architecture, to answer the agent's questions, and the security person accountable for the grades. Their git identity goes into the report as the assessor. Often this is one person.

**How long it takes.** Each report records when the run started and finished, and its page shows the duration, so after the first assessment you have your own number. What makes a run longer is missing facts: each one is a question back to you. Write down before you start what the system is made of, who can put text into it, what is worth protecting and what controls already exist. The demo description is a template for that.

[Getting started](docs/getting-started.md) walks this path step by step.

## What comes out

A report is one YAML file per system per date, and a page in the UI and on the published site. Different people read different parts of it:

| Reader | What they look at |
| --- | --- |
| Risk owner | The findings table: each threat in one paragraph, with severity and likelihood on a three-level scale |
| Product team | The requirements marked for hand-off: what to build, and what is already in place |
| Security lead, next assessor | Everything, including the threats ruled out with the reason and what changed since the last assessment |

[Reading a report](docs/reading-a-report.md) explains each part with an example.

## Run it in your own Git

Bring Keel into your internal Git host with upstream kept as a second remote, so you can take updates later:

```bash
git clone https://github.com/roselis-lab/keel.git
cd keel
git remote rename origin upstream
git remote add origin <your internal repository URL>
git push -u origin main

uv sync                 # Python 3.11 or newer; `pip install -e .` works too
uv run keel validate    # warnings for unfinished catalog cards, then "Catalog is valid."
```

The repository already carries the MCP and skill configuration for each supported agent, so opening the folder in the agent is the whole setup. CI for GitHub is in `.github/workflows/ci.yml`; for GitLab, copy [`examples/pages/gitlab-ci.yml`](examples/pages/gitlab-ci.yml).

[Adopt Keel in your company](docs/adopt.md) covers the rest: who reviews catalog changes, where reports live, and publishing the site.

## Keep your changes and still take updates

What you change in your copy:

- **`implementations`** on a control card: how your organisation actually built that control. Until one is recorded, the assessor treats the control as a recommendation, not as cover.
- **New threats and controls** for your own stack.
- **Reports**, if you keep them in the same repository.

To take upstream changes, merge `upstream/main` on a branch and open it as a pull request; CI runs `keel validate` over the result. Adding new files and implementation records merges cleanly; rewriting upstream text is what produces conflicts. [Taking upstream changes](docs/adopt.md#take-upstream-changes) has the commands.

## Share it with people who do not run Keel

```bash
uv run keel site --out public                      # the catalog only
uv run keel site --out public --reports reports    # plus the signed-off reports
```

The output is a folder of static pages with no scripts. Ready-made pipelines: [GitHub Pages](examples/pages/github-pages.yml) and [GitLab Pages](examples/pages/gitlab-ci.yml). A Pages site can be public on the internet depending on your plan, so check [who can see it](docs/adopt.md#who-can-see-the-site) before publishing reports.

To put a signed-off report where developers already work, `keel publish` turns it into a Confluence page and one Jira ticket per thing to build, with a picture of each risk, using your own token: [Confluence and Jira](docs/confluence-and-jira.md).

The local UI (`uv run keel up`, at `http://127.0.0.1:8420/`) is for the people who author: correcting reports and editing the catalog through forms. It listens on your own machine only and has no login, so it is not the thing to share.

## What is in the catalog

A snapshot, taken on 7 November 2026. `keel validate` and the site's overview page give the live numbers.

- **13 threats, 76 controls**, 105 threat-to-control links, 65 references to incidents, papers and advisories.
- **136 coverage rows** against the four tracked lists: 98 covered, 26 out of scope with the reasoning, 12 gaps. Both OWASP lists are fully answered. [The table](docs/comparison.md#coverage).

What is not done yet, stated rather than hidden:

- 279 control card fields are unwritten (`scope`, `out_of_scope`, `locus` and `failure_behavior`), across 70 of the 76 cards.
- 69 controls have no acceptance criteria. A control nobody can check is a recommendation, and `keel validate` says so in those words.
- 1 control is linked from no threat.

## Documentation

**Start here**

- [Getting started](docs/getting-started.md): from clone to your first report.
- [Reading a report](docs/reading-a-report.md): what each part means and who it is for.
- [Adopt Keel in your company](docs/adopt.md): internal Git, CI, catalog review, where reports live, publishing, upstream updates.
- [Confluence and Jira](docs/confluence-and-jira.md): a report as a page for readers and one ticket per fix, from your own machine.

**Reference**

- [Commands, skills, UI and interfaces](docs/interfaces.md)
- [The model](docs/model.md): threats, weaknesses, controls, every field and the fixed vocabularies.
- [Authoring](docs/authoring.md): how new catalog content is researched, written and checked.
- [Against OWASP, ATLAS and MAESTRO](docs/comparison.md): what Keel takes from each, and the coverage table.

**Background**

- [Why Keel is built this way](docs/why-keel.md)

## Development

Two checks, for two different things. `uv run keel validate` checks the catalog content: schema, fixed vocabularies, links, and coverage claims. `uv run pytest` tests Keel's own code.

```bash
uv sync --extra dev
uv run ruff check .
uv run keel validate
uv run pytest
```

CI runs these, plus `keel schema --check`, on every pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for what belongs in the shared catalog and what belongs in your copy.

## License

Keel is licensed under the [Apache License 2.0](LICENSE), covering the code, the catalog, the skills and the docs. Attribution is requested when reusing the catalog or the methodology. See [NOTICE](NOTICE).

The bundled `humanizer` skill is third-party work by Siqi Chen under the MIT License.
