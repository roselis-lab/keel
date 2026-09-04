# Research procedure

The card is a claim about how systems actually fail. You cannot make that claim from what you remember; model memory is a summary of the field as of a training cut-off, and it is exactly detailed enough to write something that sounds right.

So: **search the web, read the sources, then write.** Not the reverse. A reference found after the card is written is decoration, and it shows - the note under it explains what the source is rather than what it supports.

---

## What you have to come back with

Four things. Three of them are findable for most subjects; the fourth is often the most useful.

**1. At least one case where this actually happened.** An incident, a disclosed vulnerability, a postmortem, a published attack against a real deployment. Not a paper's threat model, not a vendor's marketing example, not a hypothetical. If the only thing you find is somebody's list saying the risk exists, you have found a list, not a case.

**2. What the defence turned out to be.** For an incident, the vendor's own follow-up is worth more than any recommendation, because it says what they actually shipped. A fix that ships is a control that exists; a fix that is recommended may be a control nobody can build.

**3. What the tracked sources say, in their own words.** `get_coverage` tells you which of them name the subject. Then go read that entry at the source, not our one-line summary of it. The summary is a pointer; the wording is where the difference between their entry and ours turns up, and that difference is what `positioning` has to state.

**4. What you could not find.** Say it. A subject with no incident, no advisory and no literature is not automatically absent from the model, but it is a different kind of entry, and the card has to carry less weight. Recording the absence also stops the next person repeating the search.

---

## Where to look

Roughly in the order that pays off:

- **Incident databases and postmortems.** The AI Incident Database, vendor status pages and their follow-up writeups, security advisories. This is where cases live.
- **The tracked sources at their source.** OWASP LLM and Agentic Top 10, MITRE ATLAS technique pages, Google SAIF. ATLAS in particular carries case studies attached to techniques.
- **CVE and vendor advisories** when the subject touches a product, a framework or an agent runtime.
- **Papers**, for a subject that is a research result rather than an incident - a new class of attack, a measured failure rate. Read what the paper measured, not what its abstract claims.
- **Practitioner writeups** last. Useful for how a control behaves in production and for the ways it gets implemented wrong, which is what `anti_patterns` needs. Weak as evidence that the threat is real.

Two habits that pay for themselves. Search for the *failure*, not for the *label* - "agent deleted production database" finds more than "excessive agency". And when a source cites another source, go to the cited one; a lot of writing in this field is other writing, rephrased.

---

## What a reference is for

A reference is evidence that the threat is real or that the control works. It is not a framework mapping. Which OWASP or ATLAS entry this answers is recorded once in the coverage matrix and read back from there, so a reference whose note amounts to "this is LLM01" duplicates the matrix and tells a reader nothing.

Each note says, in one line, what that source actually supports. If you cannot write that line, you have not read enough of the source to cite it.

---

## The gate

Do not start writing fields until you can answer all four of these:

1. Name a case. Where, what happened, and what made it possible.
2. Name the defence that was actually adopted, or say that none was.
3. Name what the tracked sources call this, and how their entry is shaped differently from ours.
4. Name what you looked for and did not find.

If you cannot, keep looking or say so out loud. Starting anyway produces a card that reads well and is not worth anything, and the review will not catch it - a fluent card written from memory passes every per-field bar. That is the failure this gate exists for.
