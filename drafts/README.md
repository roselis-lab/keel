# drafts/

Content that is written but not vouched for.

`catalog/` is a promise: everything in it has been read by a maintainer and is believed correct, well written, and backed by at least one reference. `drafts/` is where content waits before anyone has made that promise about it.

Nothing here is loaded by the app, served over MCP, or checked by `keel validate`. It is source material.

## Why this directory exists

The first pass at the catalog produced 13 threats and 71 mitigations quickly, and quantity turned out to be the problem. Every mitigation was marked draft, none carried a reference, most rationales were sentence fragments, and 25 links were graded `gating` while pointing at cards that are not gating controls. A reader had no way to tell the checked parts from the unchecked ones, because there were no checked parts.

Rather than fix that in place, the whole thing moved here, and `catalog/` refills one entry at a time. The rule is one direction only: an agent may write into `drafts/`, and only a person moves a file from `drafts/` into `catalog/`.

## Moving something into the catalog

Rewrite it against the style guide rather than editing it in place — most of this text was written before the authoring bar existed. Give it at least one reference with a note saying what the reference actually supports. Check every link's `strength` against the target card's `mitigation_class`. Then record which coverage entries it answers in `catalog/coverage/`.
