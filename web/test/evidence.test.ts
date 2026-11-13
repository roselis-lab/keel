// The evidence marks in report prose (src/lib/evidence.ts). Run with `npm test`: Node
// strips the types itself, so no test framework is installed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { clipQuote, splitMarks, whereLines } from "../src/lib/evidence.ts";

const held = new Set([1, 2, 3]);
const marks = (text: string) => splitMarks(text, held).filter((s) => s.id !== undefined);
const joined = (text: string) => splitMarks(text, held).map((s) => (s.id === undefined ? s.text : s.label)).join("");

test("a mark on evidence the report holds is a link to it", () => {
  assert.deepEqual(splitMarks("The tool takes the amount [1].", held), [
    { text: "The tool takes the amount " }, { id: 1, label: "[1]", broken: false }, { text: "." },
  ]);
});

test("a mark on evidence the report does not hold is broken", () => {
  assert.deepEqual(marks("A cap in the gateway [9]."), [{ id: 9, label: "[9]", broken: true }]);
});

test("a link to #ev-n keeps its words; a bare #ev-n is the mark itself", () => {
  assert.deepEqual(marks("and [the gateway call](#ev-2) sends it"), [{ id: 2, label: "the gateway call", broken: false }]);
  assert.deepEqual(marks("Nothing caps it: see #ev-3."), [{ id: 3, label: "#ev-3", broken: false }]);
  assert.deepEqual(marks("an old [note](#ev-7) and #ev-8"), [
    { id: 7, label: "note", broken: true }, { id: 8, label: "#ev-8", broken: true },
  ]);
});

test("a list of marks is one mark per number, brackets and commas kept as text", () => {
  assert.deepEqual(splitMarks("unchecked [1, 3 ,9].", held), [
    { text: "unchecked [" }, { id: 1, label: "1", broken: false }, { text: ", " },
    { id: 3, label: "3", broken: false }, { text: " ," }, { id: 9, label: "9", broken: true }, { text: "]." },
  ]);
});

test("an index, a word in brackets and an anchor in a path are not marks", () => {
  for (const t of ["reads items[3] from the queue", "matrix[1][2]", "[draft] text", "[3a]", "/doc#ev-3", "x#ev-3", "#ev-3b"]) {
    assert.deepEqual(marks(t), [], t);
  }
});

test("apart from a link, which shows only its words, the text comes back whole", () => {
  for (const t of ["", "plain", "[1] at the start", "end [2]", "[1, 2] and #ev-3, #ev-9 [9]"]) assert.equal(joined(t), t);
  assert.equal(joined("see [the call](#ev-2)."), "see the call.");
});

test("a long quote is cut by lines and by length, with its line breaks", () => {
  const q = Array.from({ length: 12 }, (_, i) => `line ${i + 1}`).join("\n");
  assert.equal(clipQuote(q, 3), "line 1\nline 2\nline 3\n…");
  assert.equal(clipQuote("short\nquote\n"), "short\nquote");
  const cut = clipQuote("word ".repeat(200), 8, 40);
  assert.ok(cut.length <= 42 && cut.endsWith("\n…") && !cut.includes("wor\n"), cut);
});

test("under the quote: path:lines, then the repository and the short commit", () => {
  assert.deepEqual(whereLines({ id: 1, kind: "read", quote: "q", repo: "payments-api", commit: "3f9c2a7d1e5b4c6a8f0e", path: "tools/refund.py", lines: "40-52" }),
    ["tools/refund.py:40-52", "payments-api @ 3f9c2a7"]);
  assert.deepEqual(whereLines({ id: 2, kind: "read", quote: "q", commit: "9d8e7f6a", path: "a.py", lines: "17" }), ["a.py:17", "9d8e7f6"]);
  assert.deepEqual(whereLines({ id: 3, kind: "command", quote: "q", command: "grep -rn max_refund ." }), ["command: grep -rn max_refund ."]);
});
