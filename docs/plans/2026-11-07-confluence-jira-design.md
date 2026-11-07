# A report in Confluence and Jira

Design, 2026-11-07. Status: built in this branch.

## The problem

Developers who have to act on a report find it hard to read: everything is in one long page, and there is no picture of how an attack works. They also do not work in Keel. Their documentation is in Confluence and their work is in Jira. So a report has to reach them there, easy to read, and the things to build have to arrive as tickets.

Keel is deployed as a tool on the assessor's machine. It is not a service with integrations. Whatever we build has to work from that machine.

## How comparable products do it

- **Threat-modelling platforms and finding managers** (IriusRisk, SD Elements, PlexTrac, DefectDojo) run as servers. A service account syncs both ways with Jira, and issue tracker profiles route each countermeasure to a team's project. What becomes a ticket is the countermeasure, not the threat. ([IriusRisk countermeasures](https://www.iriusrisk.com/documentation/countermeasures), [IriusRisk 4.27](https://www.iriusrisk.com/resources-blog/product-update-release-4-27), [SD Elements](https://docs.sdelements.com/master/guide/docs/integrations/issue_tracker_integration/understand.html))
- **Tools that run on a person's machine or in CI** push in one direction with the person's token. One example is the Threat Dragon to Jira script, which reads its credentials from a config file. Docs-as-code publishers such as md2conf, text2confl and cosmere take a personal access token from the environment and offer a dry run. cosmere also marks generated pages with a note asking readers not to edit them. ([Threat Dragon utilities](https://owasp.org/www-project-threat-dragon/docs-1/utilities), [md2conf](https://github.com/md2conf/md2conf/blob/master/README.md))
- **Ticket granularity and duplicates.** Before filing, scanner integrations search for a ticket under a stable key and either group findings by fix or file one ticket per finding. Black Duck's sync treats a duplicate ticket as worse than a late one. ([Semgrep](https://docs.semgrep.dev/semgrep-appsec-platform/jira.md), [Dynatrace on Snyk](https://www.dynatrace.com/news/blog/snyk-dynatrace-integration-actionable-notifications/), [bd-jira-sync](https://pypi.org/project/blackduck-jira-sync/0.3.1/))
- **Visibility.** Vulnerability tickets go under a Jira issue security level so that only the named group can open them. ([Atlassian](https://confluence.atlassian.com/adminjiraserver/restricting-issues-to-project-roles-1671102809.html))
- **Formats.** Confluence Cloud and Data Center both take storage format (XHTML) over REST, with an image as an attached file. Confluence Cloud does not show an attached SVG reliably. Jira's v2 API takes wiki markup on Cloud and on Data Center, and an image has to be attached before the text that shows it.

## Decisions

- **One-way push from the assessor's machine, with their own token.** We do not run a service, a service account, or two-way sync. Keel never changes a ticket's status, priority or assignee after filing it.
- **Not an agent's action.** `keel publish` is a command line only. It is not an MCP tool, not an API route and not a UI button, because sending to a company system is a person's decision. A test checks that no MCP tool publishes.
- **One ticket per thing to build**, keyed by system plus catalog control, or by root cause for a request with no card. The key becomes a hashed label, and Keel searches for that label before it files anything, so a reassessment updates the same ticket. If the label turns up on two issues, Keel stops.
- **The page is generated and says so.** The report in Git stays the record, and edits on the page are overwritten. The page reads in layers: the summary, then the table of what to build, then each risk with its picture, its two sentences and its fix. The reasoning and evidence are folded under an expand, and the ruled-out list and the open questions come last. Nothing is cut.
- **One picture per finding.** It shows the chain and where the fix cuts it. A picture carries one relationship; the rest stays in text. Keel draws it as a PNG from the report fields alone, so no model is involved. It uses the first system font found that covers Cyrillic, because the font Pillow ships has Latin letters only and a Russian report would come out as boxes. `KEEL_PICTURE_FONT` pins a font file, so the picture is the same on every machine. The local report UI shows the same picture.
- **Escaping.** Every value is escaped for XHTML and for wiki markup, and only `https` links are made. A report can quote hostile text.
- **Only final reports are published** unless `--allow-draft` is given; a draft page then says it is a draft. The same rule applies to the read-only site.
- **Dry run and export.** `--dry-run` lists what would be sent, and warns when no security level is set. `keel export` writes the same content to files.
- **Links between the two.** Keel writes the page and ticket links into `<date>.published.json` next to the report, so the next publish finds the same objects.

## Not in this change

- Two-way status sync, and closing tickets when a later report no longer needs them. Both need a service, or a decision about who owns the ticket after filing.
- Atlassian Document Format for Jira Cloud's v3 API. The v2 API with wiki markup works on Cloud and Data Center, and ADF references attached images by media id, which the API does not expose cleanly.
- A test against a live Confluence and Jira. The client is tested against a fake that checks the order of calls, the headers and versioning. A first run against a real space is still to do.
