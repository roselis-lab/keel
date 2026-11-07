# Confluence and Jira

Your developers already read Confluence and work from Jira. This page is about getting a signed-off report there: as a Confluence page for everyone who reads it, and as one Jira ticket for each thing a team has to build.

Keel runs on the assessor's machine, not as a service. So it works the way docs-as-code publishers and scanner command lines do: you run one command, with your own token, and it pushes in one direction. Keel holds no server credentials and nothing syncs back.

## What arrives

**The Confluence page** reads from the top down, and most people stop early:

1. One line on what was found: how many risks, how many things to build, what was ruled out, which questions are open.
2. **What to build:** a table of what must hold, where it is enforced, how to tell it is done, and the ticket for each item. A developer usually needs only this table.
3. **The risks**, one each. First comes a picture of the chain: who, the way in, the weak spot, the damage, and where the fix cuts it. Then two sentences, *what happens* and *why it matters*, and then the fix. The reasoning, the review and the evidence are folded under *How we know, for reviewers*. Nothing from the report is dropped.
4. **Ruled out**, with the reason for each. This is where the next review starts.
5. **Still open**: each question, with the check that settles it.

A banner at the top says the page is generated from the report file. Any edits made on the page are overwritten by the next publish, so the report stays the record.

**One Jira ticket for each thing to build**, not one for each finding. If one fix closes three findings, that is one ticket with three reasons on it. Each ticket says why the work is needed (with the same picture), what must hold, where, and when it is done; the last part is the acceptance criterion. It ends with a link to the page. After that, Keel never changes the ticket's status, assignee or priority: the ticket belongs to the team.

The same picture appears on the finding in the local report UI.

## Look before you send

```bash
uv run keel export reports/halo/2026-11-07.yaml --out out/halo
```

This writes the page in Confluence storage format, one PNG for each finding, and the text of each ticket, all to a folder. It sends nothing. Use it to read what would go out, or to hand the files to whoever owns your Atlassian setup.

## Publish

Put the token in the environment. Keel never takes it from the command line, where it would end up in your shell history.

| | Cloud | Data Center |
| --- | --- | --- |
| `KEEL_CONFLUENCE_URL` | `https://your-site.atlassian.net/wiki` | `https://confluence.your-company` |
| `KEEL_JIRA_URL` | `https://your-site.atlassian.net` | `https://jira.your-company` |
| `KEEL_ATLASSIAN_TOKEN` | an [API token](https://id.atlassian.com/manage-profile/security/api-tokens) | a personal access token |
| `KEEL_ATLASSIAN_EMAIL` | the account the token belongs to | leave unset |

If Confluence and Jira need different tokens, set `KEEL_CONFLUENCE_TOKEN` and `KEEL_JIRA_TOKEN` as well. Keel only connects over `https`.

```bash
uv run keel publish reports/halo/2026-11-07.yaml \
  --confluence-space SEC --parent 123456 \
  --jira-project HALO --security-level "Security findings" \
  --dry-run
```

`--dry-run` lists what would be created or updated and sends nothing. Run the same command without it to publish. You can give only `--confluence-space` or only `--jira-project`. Only final reports are published. `--allow-draft` publishes a draft anyway, and the page then says it is a draft.

The order matters, and Keel takes care of it. It makes sure the page exists, files or updates the tickets with a link to the page, and then writes the page with links to the tickets. The pictures are uploaded before the text that shows them; if they were not, Confluence would show "unknown attachment".

## Publishing again

Each ticket carries a label such as `keel-3f9a01c2b7de`. The label comes from the system plus the control, or, for a request with no catalog card, from the finding's root cause. It stays the same across reassessments. Before filing a ticket, Keel searches for that label and updates the ticket it finds. That means a reassessment that finds the same gap updates the existing ticket instead of opening a second one. If a label is on more than one issue, Keel stops and tells you to remove it from all of them but one.

The page is found again by its title in the space and updated as a new version, so the page history shows every publish of that report. A reassessment has a new date, so it gets its own page, while the tickets carry over.

Next to the report, Keel writes `<date>.published.json` with the page and ticket links. Commit it together with the report.

## Who can see it

Findings describe how to break a system, so decide who reads them before the first publish.

- **Jira:** pass `--security-level` with the name of an issue security level in your project, so that only the people in that level can open the tickets. Without it, the dry run warns you that anyone who can see the project can see them. Issue security levels are set up by a Jira administrator.
- **Confluence:** publish into a space or under a parent page with view restrictions. The page carries the evidence, including quoted lines of code. The tickets do not: they link to the page instead.

## Why it is built this way

- **Push from the assessor's machine, with the assessor's own token.** Two-way sync needs a service account and a server that is always running, which is what threat-modelling platforms and finding managers run. Keel is a tool on one person's machine. Running publish yourself means every ticket is filed by a person who chose to file it, under their own name, with their own permissions.
- **Only you can publish, not an agent.** Publishing is a command line only. It is not an MCP tool and not a UI button, because sending to a company system is a person's decision.
- **One ticket per fix.** A ticket for every finding floods a backlog with duplicates of one piece of work. Grouping by the fix and finding the ticket again by a stable key is how scanner integrations keep tickets countable.
- **PNG, not SVG.** Confluence Cloud does not reliably show an attached SVG. Both products show PNG everywhere.
- **Report text is escaped.** A report can quote a hostile prompt. On the page and in the ticket it shows up as text and never as markup or a link.
