"""A finished report as a Confluence page and Jira tickets, from the assessor's machine.

Keel runs on the host of the person who assesses, not as a service, so this is a one-way
push with that person's own token, the way docs-as-code publishers and scanner CLIs do
it: the report in Git stays the record, the page is generated from it and overwritten
on the next publish, and each thing to build becomes one ticket whose status then lives
in Jira. Nothing here is reachable from the HTTP API or the MCP tools: sending to a
company system is a person's decision, made by running the command.

* `render` turns a report into Confluence storage format and Jira wiki markup.
* `picture` draws one chain per finding as a PNG.
* `client` is the small REST client for Confluence and Jira, Cloud and Data Center.
* `cli` is `keel export` (files only) and `keel publish` (the push).
"""
