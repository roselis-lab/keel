# The system we assess on stage

Read this aloud, or put it on one slide and let the room read it. It is written to be complete enough that the assessor never stops to ask a question - the skill has a rule that it must halt rather than assume, and a halt in front of an audience looks like a failure even when it is the skill working correctly.

---

## Halo, the in-product support assistant

**What it does.** Halo answers questions inside our web app. A signed-in user from a customer company types a question in a side panel; Halo answers, and for four operations it acts instead of answering.

**The pieces.**

A chat panel in the product. The session carries the user's company id and role. The panel renders whatever the model returns as markdown - links and images included.

An orchestrator service that holds the prompt, calls the model, and runs the tool loop. It stops after six tool calls in a turn.

A hosted commercial model, called over the vendor's API. We call the `-latest` alias. No fine-tuning, and the contract says our data is not trained on.

Retrieval over one vector index holding three bodies of text: the public help centre, each customer's own past tickets with their attachments, and internal runbooks our support engineers write. Every row carries a company id and the query filters on it. Customer attachments are run through OCR and indexed.

Four tools. `lookup_order` reads the production database. `issue_refund` moves money, up to $500 with no human in the path; above that it files an approval task. `update_shipping_address` writes to the production database. `escalate_to_human` opens a Zendesk ticket with the transcript attached.

Memory. The last twenty turns are kept per user. On top of that, at the end of each conversation Halo writes itself a short note about the customer, and reads that note at the start of the next one.

Everything runs in our own network. The call to the model vendor is the one thing that leaves it.

**Who can put text in.** Any signed-in user at any customer company can type anything, and can upload attachments that end up in the index. Our support engineers write the runbooks; the content team writes the help centre. Nothing else can write to anything Halo reads.

**What is worth protecting.** Order and shipping data for about four thousand customer companies in one database. Money, through the refund path. The support team's hours. And standing with customers whose staff use this every day.

**What is already in place.** Single sign-on. A company-id filter on retrieval and on `lookup_order`. The refund cap. The tool-loop cap. Requests and replies go to the SIEM and are kept ninety days. The vendor's own content filter sits on the model API. We have no output filter of our own, no evaluation suite, and nobody has run a red team against it.

---

## The second architecture

After the first assessment, change four things and run it again. This is the same product on the plan we sell to small customers.

Halo answers only; the four tools are gone. It reads the help centre alone - no customer tickets, no attachments, no runbooks. It keeps no note between conversations. It is deployed one company per instance.

Nothing about the threats changed. The architecture did, and the verdicts move with it.

---

## What this will produce, so nothing on stage surprises you

Ten of the thirteen records apply to the first architecture. That is honest for a customer-facing assistant that spends money and reads text its users wrote, and it is worth saying out loud before someone in the room decides the tool just agrees with everything. The three it rules out, and the reasons, are the more interesting half.

**Ruled out, and the reachability says why in one line each.**

`T-CMD-INJECT` - no interpreter is reachable. Four tools with typed arguments, no shell, no eval.

`T-SSRF` - the tools' addresses are fixed and the model cannot influence them. The database and Zendesk are where they are.

`T-SUPPLY-DEPS` sits on the line, and this is the one to slow down on. Everything is pinned except the model, and we call the `-latest` alias, so the vendor rolls a new one under us on their schedule. Under the record's own wording that keeps it live. It is the kind of thing that is never in a threat model because it does not look like a threat when you write it down.

**Live, and worth pointing at.**

`T-CODEGEN` is the one the room will expect to be ruled out - we do not generate code. It stays live because the panel renders markdown, so a model-supplied image URL is a request the browser makes, with the session attached. The rule-out asks whether anything downstream executes the output *or renders it as active content*, and the second clause is the one that catches us.

`T-TOOL-ABUSE` on the refund path, where the harm is data integrity rather than exposure - real state changed under a wrong instruction.

`T-CROSS-TENANT` twice over: one index for four thousand companies behind a filter, and a note the assistant writes to itself that outlives the conversation.

`T-SOURCE-POISON` because customer-uploaded attachments go through OCR straight into the index.

`T-CRED-THEFT` because the orchestrator holds a database account and a Zendesk token of its own, rather than acting under the asking user's credential. That is also what makes the company-id filter the only thing standing between two customers.

**On the second architecture,** `T-TOOL-ABUSE`, `T-CRED-THEFT`, `T-HALLUCINATION` and `T-SOURCE-POISON` fall away, and `T-CROSS-TENANT` goes with the single-company deployment. Same catalog, same reachability text, different answer.
