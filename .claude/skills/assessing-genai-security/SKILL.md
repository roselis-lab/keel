---
name: assessing-genai-security
description: Use when assessing the security of an LLM system, agent, coding agent, RAG pipeline, MCP integration, assistant or a single AI feature ("threat model", "security review", "risk assessment", "модель угроз", "оцени риски", "безопасность агента"), including when the user only describes what the AI can read and do and asks what could go wrong, or asks whether a guardrail, classifier, permission mode or safety training counts as a mitigation. Not for systems without AI, writing exploits, configuring a specific tool, or writing usage policy.
---
# GenAI Security Assessment

Deliver a threat assessment for one specific system, in the order below. The reader must be able to reconstruct and dispute every conclusion from your trail.

## Output

Two parts, in this order:

1. **Analysis trail**: the threats considered, the ones discarded and on what grounds, and each surviving threat through steps 3 to 11.
2. **Final assessment**: one row per surviving threat. The scenario is one story in connected prose: source, attack surface, vulnerability, asset, harm, then what the integration changed and what the attack costs to pull off. No fact from the chain is dropped; plain language, a domain term only where it carries meaning; every sentence tied to this system.

```markdown
| Threat | Scenario | Severity × likelihood |
|---|---|---|
| T1. <short name> | <Source> with <real access> does <action> through <surface>. Because <vulnerability>, <asset> ends up <outcome>, which costs <who> <harm>. Before the integration <baseline>; the integration changed <delta>. Pulling it off takes <complexity>. | <severity> × <likelihood>; <what compensates, if anything> |
```

A complete threat with its trail and final row: [references/worked-example.md](references/worked-example.md). Open it when unsure how a chain or a row should read.

## Data-sufficiency gate

The assessment is built only on facts about the system established from the context. The context is never assumed to be complete. At any step, if a claim needs a fact that is not in the context:

1. Do not fill it in with an assumption.
2. Look for it yourself first, in what you can reach: the code, the configuration, the logs, and in an unclear case a test you can run. A fact you could have read is not a question.
3. If you know where the fact is and lack the access or the document, ask for that access or that document.
4. Otherwise stop the analysis at that exact point and ask the task-giver for the fact. Wait for the answer before continuing that branch.
5. Once you have the fact, continue from that point.

If several missing facts are visible at that moment, ask them together, but the pause stays tied to the point where they were needed.

A missing fact pauses only what depends on it. Carry every threat, measure and verdict that the established facts already decide through to the end in the same answer, and mark each paused branch with the fact it waits for. A paused branch gets no grade, no discard and no measure until its answer comes, and the assessment is not finished while any branch is paused. Violations: stopping the whole assessment at step 1 when the facts given already decide part of it; writing a branch down "for now" and grading it to be corrected later.

A branch depends on a fact when it cannot be decided without it: whether the source can reach the surface at all, whether the action or the asset exists. A compensating control or a refutation that is not verified does not pause the grade, because step 9 counts no unverified control anyway: grade the risk from the established facts with that control uncounted, ask for the fact, and say what the grade becomes if the control holds. Such a grade is not provisional, it is the grade of the system as established; a new fact changes it, as any new fact would. Violation: withholding a grade that the given facts decide, for example the likelihood of injection through an inbox anyone can write to, while waiting to hear whether some control exists.

If you run under another agent (a subagent in a larger run), return the open questions to it and wait for the answers instead of finishing the paused branches. If there is no one at all to answer, stop and return an explicit "Insufficient data to complete: …" block listing the missing facts, instead of analysis on assumptions.

## Cross-cutting rule

Security guarantees cannot be built on inference quality. An LLM does not architecturally separate control instructions from user input: it reads ordinary text as an instruction, produces unexpected outputs on clean input, and errs on filters in both directions. So every *boundary*, and every control in front of an irreversible action or an outbound channel, is architectural, outside the model. A model-based measure is never a boundary; at most it is a credited *layer* (step 11). Input is assessed separately: data-sensitivity classification, interaction design, the surface of influence. This is not a substitute for injection defense. Violation: "this input is from our internal system, injection is not relevant."

## Workflow

Copy this checklist into the trail and tick it as you go:

```
- [ ] 1. Context: assets, trust boundaries, who introduces data, baseline and deployed controls
- [ ] 2. Threat search from the system, worst output assumed; threats written as scenarios
- [ ] 3–8. Chain for each threat: source of harm, asset, surface, vulnerability, complexity, harm
- [ ] 9. Risk: likelihood × severity, refutations sought, compensating controls verified
- [ ] 10. Delta in MITRE ATLAS terms
- [ ] 11. Measures: first what an architectural restriction removes, then each measure priced against its bypass
- [ ] Discard log
- [ ] Self-check passed
```

1. **System context.** Establish context along three directions. *Assets and trust boundaries*: what exactly are we protecting (data, decisions, processes, infrastructure), and where do the trust boundaries run, the points where the trust level of data or a request changes? Threats materialize at these transitions, not inside components. *Who and what introduces into the system*: who is allowed to introduce data or control actions, not just read, and what real access do they have to the attack surface? How can the system be misused or turned against its own users? *Existing baseline*: what similar capabilities did users and the system already have before this integration, and what controls are already deployed? Mark everything not in the context as "not established" and apply the data-sufficiency gate. Violation: describing threats without establishing where the trust boundaries run, who introduces data into the system, and what existed before the integration.

2. **Threat search.** Search from the system, not from OWASP or MITRE catalogs: assume the agent's output is already maximally harmful regardless of the input (injection, hallucination, or the model's own initiative), and assess what harm this causes given the purpose and recipient of the output, the downstream systems that consume it, and the trust boundaries from step 1. Keep separately the class of threats to the LLM itself as an asset: resource and cost exhaustion (token-DoS). Leave out anything that rests on "the model shouldn't behave that way." A framework sees one class: the lethal trifecta sees exfiltration through injection and nothing without an attacker, so before leaning on a framework, name what it cannot see. State every threat as a scenario: who does what, and what is lost as a result. A capability or a change on its own is not a threat. Violation: "a developer can add a tool that calls an unapproved endpoint" names a change, not what goes wrong. Then run the chain below for each threat, tying every field to the facts of step 1. Violation: any field filled in general terms without a tie to this system.

3. **Source.** Name where the harm comes from, then characterize it. The attacker is one source among several, and for an agent the model itself is often the main one:
   - an external attacker, through content the system consumes or directly through its interfaces;
   - the supply chain: packages, models, plugins, MCP servers, skills;
   - an insider or a user misusing legitimate access, including jailbreaking the model for forbidden output;
   - an implementation error or an accidental user action;
   - the model itself, which for an agent is four distinct sources: overeagerness (it takes initiative beyond what the user would approve: deletes data, edits tests until they pass, reuses a credential it found), an honest mistake (it misjudges the blast radius or misses a failed command), injection (an external attacker's text steers it; the model is the channel), and its own goal (it pursues an objective of its own; rare in practice today).

   For an attacker, state who (external or internal; internal does not mean "access to everything", actual access is set by this system's regulations from step 1), why (a goal; without one the threat is not realistic), and what real access they have to the attack surface. For a source without an attacker, state what triggers it in this system and with which permissions it acts. The distinction carries into step 11: only some sources adapt against a measure. Violations: "an attacker could…" without stating who, with what access, and for what goal; a threat list built only from attackers.

4. **Asset.** What is under threat: data, a decision, functionality, infrastructure?

5. **Attack surface.** Where is the interaction point? Which inputs, outputs and interfaces are available to the source from step 3?

6. **Vulnerability.** What predisposing condition makes this exploitable: architectural, implementation, operational? Model behavior is not a control here: state the vulnerability as if the model takes the worst action its permissions allow.

7. **Exploitation complexity.** What does the source from step 3 really need to execute the scenario in this architecture: access and rights, preconditions, the number of steps and the need to chain them, technical skill, dependence on timing, luck, or the actions of others. Assess qualitatively (low, medium, high) with reasoning from this system. This feeds step 9 and is re-checked there.

8. **Harm.** Who loses what, and how much? A leaked dataset, a substituted decision or a disrupted process is the outcome inside the system; the harm is what that outcome costs someone: money, legal and regulatory exposure, reputation, safety. Name both, and stop only at the loss. A chain that does not reach harm is not a threat. Violation: stopping at "the data leaks", which is the outcome, not the harm.

9. **Risk.** How likely × how severe? Possibility is not probability: weigh the specific attack path in this architecture, the source's access from step 3, and the compensating controls, counting a control only if it is verified on this system (a model-based measure counts only as a layer credited at step 11). Rolled out is not holding: managed settings can merge with local ones, be skipped by another setting, or be absent on one OS. Token interception in internal infrastructure and a request-replay attack are one "possible" vulnerability with very different probabilities of realization. Check external conditions that may reduce the threat to zero (network isolation, no reachable surface, hardware limits); if unknown or unverified, that is a gap under the data-sufficiency gate, not a reason to skip the threat: a condition that decides whether the surface is reachable at all pauses the branch, and any other unverified control stays uncounted in a grade you give now. Check assumptions: what must be true for the scenario to materialize? Seek refutations, not confirmations, and verify the chain through to harm. Violation: finalizing a threat without checking which external conditions already compensate for it.

10. **Delta.** Did the threat exist before the integration? If so, state what exactly the integration changed in the chain fields, in MITRE ATLAS terminology (attack stages and tactics as a language, not technique numbers); if the threat is new, describe it in full in these terms; if there is no delta, mark the threat **legacy**: it belongs to the existing model and is not an argument against the integration, and it stays in the assessment with its grade and measures, because the problem is real whoever introduced it. Violations: counting a threat against the integration without showing what it changed in the chain and how that reads in MITRE terms; dropping a threat because it existed before.

11. **Risk reduction.** What measure reduces this? Ask first whether an architectural restriction can remove this class of action altogether (no production credentials, no direct write, a reviewed pipeline that applies the change instead of the agent); if it can, that restriction is the first measure, and everything after it covers what remains. Architectural controls outside the model bound the harm. A model-based measure (action classifier, guardrail filter, monitor, safety training of the acting model, system-prompt instruction; none of them ever guards an irreversible action) is credited only as a *layer*, after the test in [references/model-measures.md](references/model-measures.md); open it whenever such a measure is proposed, credited, or about to be banned. Before writing a requirement, price the bypass: if the people the requirement lands on have a cheap, invisible way around it (installing the blocked MCP server on their own machine, pasting the data into a public chatbot), the requirement does not reduce the risk, it relocates it to where nobody is watching. A requirement whose bypass is cheaper than compliance is written as a gap, with the bypass named, not as a control. A ban has a bypass too: removing an action classifier leaves manual approval, which users grant to most prompts, or a personal tool outside every control. Violations: recommending a gate on the sanctioned path without asking what the unsanctioned path costs; banning a model-based measure without naming what replaces it.

End the trail with the discard log: what was removed at steps 2, 8 and 9, and why.

## Self-check before the final table

Check the trail against each line; fix what fails and check again until every line holds:

- every threat is a scenario that reaches harm, not a capability or a change;
- every chain field rests on a fact from step 1, or the missing fact was asked for;
- every branch the established facts decide is finished and graded, each paused branch names the fact without which it cannot be decided and carries no grade, no grade is withheld only because a control is unverified, and every question was asked only after looking for the fact yourself;
- every source of harm is named; an attacker with who, access and goal, a source without an attacker with what triggers it and with which permissions it acts;
- every compensating control counted at step 9 is verified on this system;
- every measure has its bypass priced, and every model-based measure has a recorded credit or zero credit;
- every threat counted against the integration shows its delta, and a threat with none is kept as legacy, not dropped.
