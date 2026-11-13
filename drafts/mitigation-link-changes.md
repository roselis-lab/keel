# Link changes left for a threats pass

The `catalog/mitigations` changes in the same pull request as this file leave threat files alone, because another change was editing `catalog/threats/*` at the time. This is the list of link edits that pass should make. Each entry names the threat, the weakness it answers (quoted by its opening words), the strength, and a draft rationale. Delete this file once the edits land.

## New cards that no threat links yet

| Card | Threat | Weakness | Strength | Rationale (draft) |
|---|---|---|---|---|
| CTRL-SYSTEM-BOUND-RECIPIENT | T-DATA-LEAK | "A tool sends data to a destination outside the perimeter, with the destination taken from the model's own arguments" | gating | For addressed delivery (mail, chat, shares) the recipient comes from task state or a directory entry the handler resolves, so the model has no field to name an outside audience in. Network destinations stay with CTRL-URL-ALLOWLIST. |
| CTRL-SYSTEM-BOUND-RECIPIENT | T-DATA-LEAK | "A saved instruction is restored into a later context" | gating | The audience a saved instruction names cannot be reached when recipients are bound to the current task, whatever the restored text says. |
| CTRL-VERSION-BOUND-APPROVAL | T-TOOL-ABUSE | "The execution API can set a protected record to approved or apply its change without atomically checking" | gating | The apply operation checks, atomically with the write, an approval and check results recorded for exactly that version, so a skipped check or a stale approval refuses the change. |
| CTRL-INDEPENDENT-APPROVER | T-TOOL-ABUSE | "One effective principal can submit and approve the same protected change" | gating | Approvals are counted between the people each identity resolves to, so a second agent or credential of the author is not a second approver. |
| CTRL-RUNTIME-RENDERED-APPROVAL | T-TOOL-ABUSE | "The confirmation step shows the person text the model wrote" (added by roselis-lab/keel#48) | gating | The view is drawn from the call the dispatcher will execute, in full, and the digest of what was shown must match what runs. |
| CTRL-AGENT-CONFIG-PROTECTION | T-TOOL-ABUSE | "The file that holds the agent's own permissions ... is writable by the same file tool" (added by #48) | gating | No tool the agent has can write permission-bearing configuration, and a running session does not apply changes to it. |
| CTRL-RESOLVED-PATH-CHECK | T-TOOL-ABUSE | "A file tool is granted one directory, and the tool's own path check is the only thing holding it there" (added by #48) | gating | Access is decided on the resolved path by components, opened without following links, so a model-supplied path cannot leave the grant. |
| CTRL-SERVER-HELD-HISTORY | T-TOOL-ABUSE | "The conversation history is taken from the client with each request" (added by #48) | gating | The server builds context from its own record and accepts only a new user turn, so a forged assistant turn or approval is never read as history. |
| CTRL-RENDER-DESTINATION-ALLOWLIST | T-DATA-LEAK | "The client that displays the reply fetches what the reply references as it renders" (added by #48) | gating | The client fetches only from listed destinations that do not forward, so an address the model composed is never requested. |
| CTRL-RENDER-DESTINATION-ALLOWLIST | T-DATA-LEAK | "The reply can carry a link whose address the model composed" (added by #48) | gating | Links show their full destination and an unlisted one opens only after the reader sees where it goes. Leaves a reader who clicks anyway; say so in the rationale. |
| CTRL-CLOAKING-DETECTION | T-SOURCE-POISON | "The agent fetches pages live with a client a site can tell apart from a person's browser" (added by #48) | soft | A detector: it raises a mismatch and holds actions driven by the page, but it does not stop the agent reading the cloaked content. |

The #48 weakness "Output is displayed and passed on with characters a reader cannot see" belongs to CTRL-OUTPUT-ENCODING, not to a new card.

## Existing cards whose links should change

- **CTRL-TOKEN-PROTECTION on T-CRED-THEFT.** The card is now about credentials kept out of an agent's shell, files and context. Rewrite the rationale on the crossing weakness accordingly: it closes the agent's environment as the uncontrolled place; a credential crossing into a browser or client machine is not this card. Also link it to T-DATA-LEAK: "A tool with filesystem access reads files that hold secrets" (gating) and "The runtime appends confidential metadata or credentials to model-visible request fields" (gating).
- **CTRL-COMMAND-SANDBOX on T-CMD-INJECT.** Add to the rationale that it holds only where the commands can be enumerated. Link CTRL-CODE-SANDBOX to the same weakness ("A tool exposes an interpreter directly", gating) for agents that must run arbitrary build commands.
- **CTRL-URL-ALLOWLIST.** Its purpose now covers outside destinations as well as internal ones. The existing links on T-SSRF and T-DATA-LEAK still read correctly; nothing to change unless a rationale says "SSRF" as if that were the whole card.

## Merges by the splitting test

The style guide's test: two controls are two cards only if an organisation could adopt one without the other.

- **CTRL-HUMAN-IN-LOOP into CTRL-RISK-BASED-APPROVAL.** A person deciding on critical agent actions is the high-tier half of risk-based approval; nobody adopts one without the other. Move its links on T-TOOL-ABUSE and T-HALLUCINATION to CTRL-RISK-BASED-APPROVAL (keep the T-HALLUCINATION rationale's own wording about what a person reviews), drop the duplicate rationale on T-TOOL-ABUSE, then delete the card.
- **CTRL-HACT-CRITICAL into CTRL-RISK-BASED-APPROVAL.** "Regardless of other settings" is already in the risk-based approval mechanism: a session-wide grant does not satisfy the gate where every call is decided individually. Move or drop its T-TOOL-ABUSE link, then delete the card.
- **CTRL-IRREVERSIBLE-ACTION-GUARD, split.** Its separate confirmation and correlation id are risk-based approval. Its grace period, during which the action can still be cancelled, passes the splitting test: an organisation can delay and allow undo without a person deciding first. Either rewrite the card as that corrective control (delayed execution with a cancellation window) or delete it; move its T-TOOL-ABUSE link accordingly.
- **CTRL-ARG-VALIDATION into CTRL-TOOL-CALL-VALIDATION.** Same control: JSON schema, runtime guards and reference types are three ways to state the tool's contract. Reference types are now part of CTRL-TOOL-CALL-VALIDATION's scope. No threat links CTRL-ARG-VALIDATION; delete the card.

Coverage rows to update with those merges: `catalog/coverage/eu-ai-act.yaml` (lines naming CTRL-HUMAN-IN-LOOP, CTRL-HACT-CRITICAL, CTRL-IRREVERSIBLE-ACTION-GUARD) and `catalog/coverage/mitre-atlas.yaml` (CTRL-HUMAN-IN-LOOP, CTRL-IRREVERSIBLE-ACTION-GUARD). `keel/services/report_service.py` names CTRL-HACT-CRITICAL in a docstring example only.
