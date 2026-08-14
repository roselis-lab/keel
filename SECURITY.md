# Security Policy

Keel is a threat-modeling tool, so we hold its own security to the same bar.

## Reporting a vulnerability

Report vulnerabilities privately, not in public issues. Use GitHub's [private vulnerability reporting](https://github.com/roselis-lab/keel/security/advisories/new) (the Security tab, then "Report a vulnerability"). Include a description, reproduction steps, and the impact.

We aim to acknowledge a report within a few days and to agree on a disclosure timeline with you before anything goes public.

## Scope

In scope: the code (MCP server, REST API, CLI, browse UI), the catalog build and validation, and the packaging. The threat catalog content is knowledge rather than a running system, so corrections to it go through normal [issues and pull requests](CONTRIBUTING.md).

## Supported versions

Keel is pre-1.0. Fixes land on the latest `main`; there are no backported release branches yet.
