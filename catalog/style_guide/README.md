# The style guide for the style guide

This governs every element in the catalog, and the other style guides in this directory. It is the general layer: the specific guides (a vocabulary's values, a threat's or a mitigation's fields) are instances that must obey it.

The catalog is run, not read: its job is to drive an assessment of a real system. So the test for anything in it is not "is this true?" or "is this well-defined?" but "does it change what an assessment does?" Anything that changes nothing is not neutral: it is another thing to author, keep consistent, and argue about, and it misleads a reader into thinking it matters.

The elements it governs come in two kinds: a **value in a controlled vocabulary** (like `surface` or `harm`), and a **prose field on an entity** (like `weakness.text` or `mitigation.control_mechanism`). The rules below hold for both, and for any entity added later. Where a rule differs by kind, that is called out.

## Admission tests, in order

Every element passes all three, in this sequence.

### 1. One job

The element does exactly one job and does not restate a sibling.

- *For a vocabulary value:* it comes from its facet's single principle of division. `surface` is *which boundary*, `source` is *who drives it*, `component` is *where the weakness sits*, `harm` is *what breaks*. A value that smuggles in a second axis (a `source` that is really a `harm`) fails here.
- *For a prose field:* it holds only its own content. Text in `weakness.text` that names the consequence belongs in `harm`, not here.

This is the most common defect and the cheapest to miss, so it is tested first.

### 2. Warrant: does it change an assessment?

The element changes what an assessor does, through one of four lenses: candidate match, reachability, mitigation selection, or risk. Name the lens. That sentence is the element's reason to exist, and it is stored with it.

The test is deterministic: take two systems identical except for this element's content, and show the assessment comes out different: a different candidate matched, a different reachability verdict, a different control pulled, or a different risk. If you cannot construct that pair, the element does not discriminate.

### 3. No gap

The siblings together leave no assessment-relevant gap.

- *For a vocabulary:* the values are collectively exhaustive over real cases. A value that fails the warrant test is still kept if, and only if, a real case has no other correct home in its facet: a genuine threat from the source material (OWASP, ATLAS, a CVE, a recorded incident), not a hypothetical. Mis-filing corrupts assessments downstream, so keeping it is cheaper than the gap. If no such orphan case exists, cut it, and prefer one explicit residual value over a scatter of rarely-used ones.
- *For an entity's fields:* the fields together capture everything an assessment needs from that entity. A missing field is a gap the same way a missing vocabulary value is.

## A rule is admitted after it has caught something

The three tests above judge a candidate rule. This one decides whether there is a candidate at all.

**A rule is written after it has caught a real record, never because someone imagined a way to go wrong.** Name the record it caught. That record is also the example the shape below asks for, so the requirement costs nothing extra: if you cannot name one, you have not found a defect, you have found a worry.

The reason is arithmetic. A rule invented from a worry is paid for on every record ever authored, and it caught nothing. A guide that grows this way is not stricter, it is longer, and length is what makes a bar stop being read.

Two things this rules out, both of which look like diligence:

- **A rule per clumsy record.** If the wording is poor but the shape is right, fix the record. "Privilege abuse / credential theft" joins two phrasings of one outcome with a slash; it reads badly and it is structurally correct, so it is an edit, not a rule.
- **Symmetry.** A rule added because a sibling field has one, or because a case is theoretically possible, has caught nothing by definition.

The same evidence is what justifies keeping a rule. A rule that has caught nothing in a long while is a candidate for removal, judged the same way it was admitted.

## Record the warrant, do not just enforce it

Every element carries three things: a scope note an author or assessor can apply the same way twice, the assessment lens it feeds, and one real example case that needs it.

They are not a separate ceremony, and there is no slot for them, because a requirement with nowhere to live is one nobody meets. Each lands in a slot that already exists and is already read:

- The **scope note** and the **lens** are the `purpose`. One sentence: what the element's single job is, and which of the four lenses it feeds - candidate match, reachability, mitigation selection, or risk. A `purpose` that describes the field without naming a lens has not recorded a warrant, it has restated the field name at greater length.
- The **example case** is `examples`, and it is the record the rule caught when it was admitted.

This is what makes the catalog auditable by someone who was not in the room when it was written.

## For controlled vocabularies

Two rules apply only to vocabularies.

A frozen vocabulary needs a corpus and an exit. A frozen set is only as good as the real cases it has been shown to classify, and completeness is demonstrated by classifying actual threats, not by reasoning about symmetry. So a freeze comes with a coverage corpus and a written rule for what to do when nothing fits: file it under the residual value and open a change, which requires sign-off.

The guidance for one value has this shape:

- **Definition.** What it is, in one sentence.
- **Assessment impact.** What choosing it does, named against a lens. This is the heart of the entry. Write the consequence of the choice, not the neatness of the pick.
- **Disambiguation.** "Not when… → the sibling it gets confused with." Kept even when it barely moves risk, because its job is to stop authors from conflating two concepts, and that protects assessment quality upstream.
- **Reference.** A list of sources, each a title and a URL.

## For prose fields

The guidance for one field has this shape:

- **Purpose.** The one job the field does and the assessment lens it feeds, in a sentence. This is where the warrant is recorded.
- **Content requirements.** What a good entry must contain, each requirement checking something the others do not.
- **Avoid.** The specific ways the field gets filled wrong, including content that belongs in a sibling field. Each one names a record it caught.
- **Examples.** One or two real entries that meet the bar, drawn from the catalog rather than invented.

## For the record as a whole

An entity also has a bar that belongs to no one field: what counts as one record, and what to settle before writing anything. It is `purpose` (what one record of this entity is, and the lens that makes the count matter), `instructions` (what to settle first, and in what order), and `avoid` (shapes the record does not come in).

It exists because a rule about whether a record should exist has no field to live in. Parked in one it is invisible to anyone reading another; copied into several it goes stale in all but the last. The same admission tests apply, and the warrant is usually the reachability lens, since most record-shape defects show up as a rule-out verdict that is true of part of the record and not the rest.

## How the guidance reads

Guidance is reference and explanation, never a tutorial. It is action-oriented and uses the fewest words that do the job. State the condition that makes something apply before the instruction that applies it. Plain words, no coined terms: it is read under pressure, in the middle of an assessment.

## References

A reference is a title and a URL. References earn their place by auditability, since a reviewer has to be able to verify a claim against its source, not by discriminating an assessment. Judge them by that, and do not try to justify a reference by the warrant test it was never meant to pass.

## Grounded in

- ANSI/NISO Z39.19-2005 (R2010), *Guidelines for the Construction, Format, and Management of Monolingual Controlled Vocabularies*. Warrant for including a term, scope notes, disambiguation. https://www.niso.org/publications/ansiniso-z3919-2005-r2010
- Howard & Longstaff (1998), *A Common Language for Computer Security Incidents*, Sandia SAND98-8667. The criteria a security taxonomy is judged by, including *useful* and *exhaustive* as co-equal. https://nsarchive.gwu.edu/sites/default/files/documents/4530309/John-D-Howard-Thomas-A-Longstaff-Sandia-National.pdf
- Hansman & Hunt (2005), *A Taxonomy of Network and Computer Attacks*. Determinism of the classifying procedure; completeness proven by classifying real attacks. https://www.researchgate.net/publication/222658152_A_taxonomy_of_network_and_computer_attacks
- Ranganathan's facet analysis, via Broughton, *Facet Analysis: The Evolution of an Idea*. A facet is divided by a single characteristic; facets are orthogonal. https://www.tandfonline.com/doi/full/10.1080/01639374.2023.2196291
- DCMI, *The Singapore Framework for Dublin Core Application Profiles*. Every element traces to a functional requirement; metadata exists to support an activity. https://www.dublincore.org/specifications/dublin-core/singapore-framework/
- Procida, *Diátaxis*. Documentation organized around what the reader is trying to do. https://diataxis.fr/
- Carroll, *The Nurnberg Funnel* (1990). Minimalist, task-oriented documentation. https://en.wikipedia.org/wiki/Minimalism_(technical_communication)
