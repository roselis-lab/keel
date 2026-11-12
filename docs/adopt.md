# Adopt Keel in your company

This page is for the person setting Keel up for a team: a security lead or a platform engineer. It covers the decisions you make once. Running an assessment is in [Getting started](getting-started.md).

## The shape

One internal copy of Keel on your Git host, used three ways:

| Who | Does | Through |
| --- | --- | --- |
| Assessors | Run assessments, correct and finalize reports | Their coding agent, and the local UI on their own machine |
| Catalog reviewers | Approve changes to threats and controls | Pull requests (merge requests on GitLab) and CI |
| Everyone else: risk owners, product teams, auditors | Read the catalog and the signed-off reports | A read-only site published with GitHub Pages or GitLab Pages |
| Product teams that live in Atlassian | Read the report and build the fixes | A Confluence page and one Jira ticket per fix, pushed by the assessor with `keel publish` ([Confluence and Jira](confluence-and-jira.md)) |

Nothing in this needs a server you run. The catalog and the reports are files in Git, review happens on the Git host, and the shared view is static pages or a page and tickets pushed from the assessor's machine.

## Bring Keel into your Git

Make an empty repository on your internal host, then:

```bash
git clone https://github.com/roselis-lab/keel.git
cd keel
git remote rename origin upstream
git remote add origin <your internal repository URL>
git push -u origin main
```

`upstream` stays pointed at the public project, which is how you take updates later. This works the same on GitHub Enterprise, GitLab and Bitbucket.

Two things to avoid:

- **A GitHub fork of the public repository.** A fork of a public repository is public. Your catalog changes and anything else you commit would be visible to everyone.
- **Copying the files without the history.** It works on day one, but every upstream update becomes a manual diff.

Install needs Python 3.11 or newer and access to PyPI or your internal mirror. `uv sync --frozen` installs exactly the versions in `uv.lock`. A container image is also available: `docker compose up` serves the local UI at `http://localhost:8000/`.

## CI

The checks are the same everywhere: `ruff check`, `keel schema --check`, `keel validate` and `pytest`.

- **GitHub:** `.github/workflows/ci.yml` is already in the repository and runs on every pull request.
- **GitLab:** copy [`examples/pages/gitlab-ci.yml`](../examples/pages/gitlab-ci.yml) to `.gitlab-ci.yml`. Its `keel-check` job runs the same checks on every merge request. If runners cannot reach PyPI, set `PIP_INDEX_URL` and `UV_INDEX_URL` to your mirror.

`keel validate` fails the pipeline on errors (a broken link between records, a value outside the fixed vocabularies, a coverage row naming a record that no longer exists) and only prints warnings for unfinished cards. Once your team has finished the cards it cares about, `keel validate --strict` turns warnings into failures too.

## Who reviews catalog changes

Make the security team the required reviewers of the catalog with a CODEOWNERS file (`.github/CODEOWNERS` on GitHub, `.gitlab/CODEOWNERS` on GitLab):

```
/catalog/                 @your-org/appsec
/catalog/style_guide/     @your-org/appsec-leads
```

Then require code owner approval on `main`: branch protection on GitHub, protected branch settings on GitLab (code owner approval needs GitLab Premium or above).

What a reviewer checks that CI cannot:

- **One threat is one harm.** A new threat should not be the same harm as an existing one reached by another path. That belongs as a new weakness on the existing threat.
- **The "does not apply when" sentence is a real condition** someone can test against an unseen system, not a restatement of the title.
- **Every reference says what it supports.** A link with no note is not evidence.
- **The wording meets the style guide.** The `check-style` skill applies it; ask the agent to run it on the changed records.

Agents may write into `drafts/`. Only a person moves a record from `drafts/` into `catalog/`. See [Authoring](authoring.md) for how new content is researched before it is written.

## What to change in your copy

In order of how much value they add and how little they cost at merge time:

1. **Implementations.** On a control card, record how your organisation built that control: what, where, who owns it. This is what lets an assessment say "already in place" instead of recommending something you have. `implementations` is the last field of every card file, so your lines sit at the bottom and upstream edits higher up the card usually merge without a conflict.
2. **New threats and controls** for your own stack, as new files. A new file never conflicts.
3. **Corrections to upstream text.** These are the edits that conflict when upstream changes the same lines. If the correction is right in general, send it upstream (see the end of this page) so you stop carrying it.

Avoid deleting upstream records you do not need. A threat that does not apply to your systems is ruled out in each assessment with the reason; deleting it means a conflict the next time upstream edits it.

## Where reports live

A report holds real system names and findings. Upstream Keel lists `reports/` in `.gitignore`, so a report can never land in a public pull request by accident. In your company, pick one of two places:

| | In your internal copy | In a separate private repository |
| --- | --- | --- |
| Set up | Delete the `reports/` line from `.gitignore` | Clone it next to Keel and set `REPORTS_DIR=../keel-reports` in `.env` |
| Pick it when | Everyone who can read the catalog may read the findings | Findings need a narrower audience than the catalog |
| Publish with the site | `--reports reports` | The pipeline checks out both repositories and passes `--reports` the second one |

Either way the assessor commits the report after finalizing it, and Git history is the audit trail of who changed what.

If reports live in your copy, never send a pull request upstream from your `main`: it would carry them. Contribution branches start from `upstream/main` (see the end of this page).

## What the organisation keeps between assessments

Some answers hold for more than one system: what the shared LLM gateway does with a prompt, which data class counts as personal, where restricted data may go. Without a place for them, every assessment asks the same people the same questions. Keep them in `org/`, one YAML file per platform or policy, next to `reports/` (or wherever `ORG_DIR` points). Like `reports/`, upstream ignores `org/`, so pick the same place for it as for your reports.

Each fact says what is true, who confirmed it and on what day, what it rests on (a link to a document, or code pinned the way report evidence is), and optionally which systems rely on it. [`examples/org/llm-gateway.yaml`](../examples/org/llm-gateway.yaml) is a made-up file to copy; `schema/org_facts.schema.json` gives an editor autocomplete.

```yaml
title: Acme LLM gateway
kind: platform            # or policy
about: The internal proxy every Acme service uses to call a model provider.
facts:
  - id: restricted-stays-internal
    statement: A call tagged "restricted" goes to the self-hosted model only.
    confirmed_by: Sam Example, security architect
    confirmed_on: 2026-10-02
    documents: [Acme data classification policy, version 4, section 3]
    systems: [support-bot]          # optional
```

How an assessment uses them:

- At the start it reads every fact (`list_reports` returns them as `org_facts`) and asks the specialist once about the ones that apply: confirmed by whom on what date, still true?
- It cites a confirmed fact as `org:<file>#<fact-id>`, the way it cites code. A threat ruled out because of a fact names the fact in its reason, so when the fact stops holding you can find what it ruled out. Saving a report that cites a fact no file holds says so.
- At the end it proposes new or changed facts as edits to these files. A person makes the edit and commits it. The agent does not write here.
- `keel recheck org/<name>.yaml --repo <checkout>` says whether the code a fact rests on is still in place, as it does for a report.

A fact is not a control marked done and Keel does not grade on it by itself. How a control is built in your organisation still belongs on the control card, in `implementations`.

## Publish the read-only site

`keel site` builds a folder of plain HTML pages: an overview, every threat and control, the coverage table and, if you ask for them, the reports.

```bash
uv run keel site --out public                                       # catalog only
uv run keel site --out public --reports reports                     # plus final reports
uv run keel site --out public --reports reports --include-drafts    # plus drafts, marked as drafts
uv run keel site --out public --title "Acme AI threat model"        # your name on every page
```

What the pages are and are not:

- **Read-only and static.** No scripts, no forms, nothing fetched from anywhere else; each page carries a Content-Security-Policy that says so. A reference link sends no referrer, so your internal address does not leak to the site being linked.
- **Built from validated records.** A report that does not match the schema is skipped with a message, and every value is escaped, so a report quoting an attack payload shows it as text.
- **Reports only when asked.** Without `--reports` no finding is published. Without `--include-drafts` only final reports are.
- **Safe to rebuild.** The command empties its output folder first, but only a folder it built itself or an empty one.

Ready-made pipelines build the site on every push to `main`:

- GitHub Pages: copy [`examples/pages/github-pages.yml`](../examples/pages/github-pages.yml) to `.github/workflows/pages.yml`, then set Settings > Pages > Source to "GitHub Actions".
- GitLab Pages: [`examples/pages/gitlab-ci.yml`](../examples/pages/gitlab-ci.yml), the same file as the CI above. Its `pages` job publishes `public/`.

Both examples publish the catalog only. Add `--reports reports` once you have checked who can see the site.

### Who can see the site

This decides whether reports can go on it.

| Git host | Who can open the Pages site |
| --- | --- |
| GitHub Enterprise Cloud | People with read access to the repository, if the site's visibility is set to private. With Enterprise Managed Users, sites can only be private. |
| GitHub Free, Pro or Team | Anyone on the internet, even when the repository is private. Publish the catalog only. |
| GitHub Enterprise Server | Not the public, unless your administrator turned on public Pages for the instance. |
| GitLab (all tiers, GitLab.com and self-managed) | Project members, once Pages access control is on for the project. On a self-managed instance an administrator has to enable the feature first. |

Sources: GitHub, [Changing the visibility of your GitHub Pages site](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site) and [Configuring GitHub Pages for your enterprise](https://docs.github.com/en/enterprise-server@latest/admin/configuring-settings/configuring-user-applications-for-your-enterprise/configuring-github-pages-for-your-enterprise); GitLab, [Pages access control](https://docs.gitlab.com/user/project/pages/pages_access_control/).

### Why a static site and not a shared server

What a team does with Keel day to day is read: a lead reads a report, a risk owner is shown one, a reviewer reads a catalog change. Writes happen in two places only: an assessor's own machine, and pull requests. A static site covers the reading with no server to run, patch or put a login in front of, and it reuses the access control your Git host already enforces. The local UI stays as the authoring tool. It writes files and has no login, which is why it listens only on `127.0.0.1` and refuses writes that come from other sites. Do not put it on the network; if you ever must, put an authenticating proxy in front of it and add the proxy's name to `ALLOWED_HOSTS`.

## Take upstream changes

```bash
git fetch upstream
git checkout -b sync/upstream
git merge upstream/main
uv sync
uv run keel validate
git push -u origin sync/upstream
```

Open the branch as a pull request. Reviewers read what upstream changed in the diff, and CI checks the merged catalog.

When the merge stops on a conflict, it is almost always a card whose text you edited and upstream edited too. Keep upstream's text unless your edit was a correction that is specific to you. If `keel validate` fails after the merge, upstream has changed the schema or a vocabulary; the error names each record that no longer fits.

There is no fixed cadence. Take updates when upstream changes something you need, and before a round of assessments, so they run against the current catalog.

## Send a fix back upstream

If you corrected a threat or a control in a way that is right for everyone, contribute it so you stop carrying the change:

```bash
git fetch upstream
git checkout -b fix/t-tool-abuse-wording upstream/main
git cherry-pick <the commit that changed only catalog files>
git push <your public fork> fix/t-tool-abuse-wording
```

Then open a pull request against `roselis-lab/keel`. Only catalog changes go upstream: never reports, never implementation records that describe your own systems. [CONTRIBUTING.md](../CONTRIBUTING.md) says what belongs in the shared catalog.
