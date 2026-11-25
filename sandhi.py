"""Transparent starter vowel-sandhi rules; deliberately not a full Sanskrit grammar."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Rule:
    name: str
    left: str
    right: str
    output: str
    note: str

RULES = [
    Rule("Savarna dīrgha", "a", "a", "ā", "Like vowels combine as a long vowel (starter subset)."),
    Rule("Savarna dīrgha", "ā", "a", "ā", "Like vowels combine as a long vowel (starter subset)."),
    Rule("Savarna dīrgha", "a", "ā", "ā", "Like vowels combine as a long vowel (starter subset)."),
    Rule("Savarna dīrgha", "i", "i", "ī", "Like vowels combine as a long vowel (starter subset)."),
    Rule("Savarna dīrgha", "u", "u", "ū", "Like vowels combine as a long vowel (starter subset)."),
    Rule("Guṇa", "a", "i", "e", "a/ā + i/ī → e; this entry covers the short-vowel starter case."),
    Rule("Guṇa", "a", "u", "o", "a/ā + u/ū → o; this entry covers the short-vowel starter case."),
    Rule("Vṛddhi", "a", "e", "ai", "a/ā + e/ai → ai; starter case."),
    Rule("Vṛddhi", "a", "o", "au", "a/ā + o/au → au; starter case."),
]
def apply(left: str, right: str):
    matches = [r for r in RULES if r.left == left and r.right == right]
    return [{"rule":r.name, "result":r.output, "explanation":r.note} for r in matches]
def analyze(word: str):
    """Find possible two-part splits matching a listed rule; output is intentionally ambiguous."""
    found = []
    for r in RULES:
        for i in range(1, len(word)):
            if word[i-1:i+len(r.output)-1] == r.output:
                found.append({"rule":r.name, "surface":word,
                              "possible_underlying":word[:i-1] + r.left + " + " + r.right + word[i+len(r.output)-1:],
                              "explanation":r.note})
    return found
