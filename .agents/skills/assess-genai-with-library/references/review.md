# Refuting a finding

The brief for step 8. A reviewer who did not raise the finding tries to break it. Agreement is cheap and proves nothing; a finding that survives a real attempt to break it is worth a `high`. Give a fresh subagent this file, the finding, the evidence entries it cites, the surface ledger, and read access to the same code. Do not give it your trail or your reasoning: it would inherit the same blind spot.

## What the reviewer does

1. **Re-read every cited line.** Open each evidence entry at its commit, path and lines. The quote must be there, and must say what the finding claims it says. A quote that is there but means something else breaks the finding as surely as one that is missing.
2. **Walk the chain link by link** and try to break each one with a fact from the code or configuration:
   - can this source reach this surface at all, with the access the finding gives it;
   - does the vulnerability hold in this architecture, for the worst action the permissions allow;
   - does the outcome happen, or does something on the way stop it (a check, a type, a scope, a person who must approve);
   - does the outcome cost someone the harm named, at the severity given ([grading.md](grading.md));
   - is a control the finding ignores in place and verified, and does the path defeat it or only weaken it.
3. **Look for what the ledger missed.** Entry points, tools and data paths in the code that are not in `surfaces`.
4. **Return** one verdict per finding and a list of missed surfaces:
   - `stands`: no link broke; say which ones you tried and with what;
   - `weakened`: a link holds only partly; say which, the fact, and the grade you would give;
   - `refuted`: a link does not hold; say which, with the fact and its evidence.

A verdict without the fact behind it is not a verdict. If breaking a link needs a fact you cannot reach, return it as an open question for the assessor, the same way the methodology's gate does.

## What the assessor does with it

`stands` and `weakened` go into the finding's `review` (`by`, `verdict`, `note`), and a weakened finding is regraded. `refuted` moves the finding to `discarded` with `by: review`, the reviewer's reason and evidence. New surfaces go into the ledger with `found_by: review` and through steps 4 to 7. The specialist can be the reviewer instead of a subagent; then `by` names them.
