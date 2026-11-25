"""PLC's explicit, inspectable starter engine for selected external vowel sandhi.

Scope: boundary-level vowel combinations only. This is not a complete
Aṣṭādhyāyī interpreter and does not model all adhikāras, anuvṛtti, exceptions,
morphology, accents, or rule-conflict resolution.
"""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass(frozen=True)
class SandhiRule:
    rule_id: str
    sutra: str
    name: str
    left: tuple[str, ...]
    right: tuple[str, ...]
    replacement: str
    explanation: str
    priority: int

RULES = [
    SandhiRule("VOWEL-001","6.1.101","Savarna dīrgha",("a","ā"),("a","ā"),"ā","a/ā + a/ā → ā",10),
    SandhiRule("VOWEL-002","6.1.101","Savarna dīrgha",("i","ī"),("i","ī"),"ī","i/ī + i/ī → ī",10),
    SandhiRule("VOWEL-003","6.1.101","Savarna dīrgha",("u","ū"),("u","ū"),"ū","u/ū + u/ū → ū",10),
    SandhiRule("VOWEL-004","6.1.101","Savarna dīrgha",("ṛ","ṝ"),("ṛ","ṝ"),"ṝ","ṛ/ṝ + ṛ/ṝ → ṝ (starter interpretation)",10),
    SandhiRule("VOWEL-005","6.1.87","Guṇa",("a","ā"),("i","ī"),"e","a/ā + i/ī → e",20),
    SandhiRule("VOWEL-006","6.1.87","Guṇa",("a","ā"),("u","ū"),"o","a/ā + u/ū → o",20),
    SandhiRule("VOWEL-007","6.1.87","Guṇa",("a","ā"),("ṛ","ṝ"),"ar","a/ā + ṛ/ṝ → ar",20),
    SandhiRule("VOWEL-008","6.1.88","Vṛddhi",("a","ā"),("e","ai"),"ai","a/ā + e/ai → ai",30),
    SandhiRule("VOWEL-009","6.1.88","Vṛddhi",("a","ā"),("o","au"),"au","a/ā + o/au → au",30),
    SandhiRule("VOWEL-010","6.1.77","Yaṇ",("i","ī"),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"y","i/ī before a vowel is replaced by y",40),
    SandhiRule("VOWEL-011","6.1.77","Yaṇ",("u","ū"),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"v","u/ū before a vowel is replaced by v",40),
    SandhiRule("VOWEL-012","6.1.77","Yaṇ",("ṛ","ṝ"),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"r","ṛ/ṝ before a vowel is replaced by r",40),
    SandhiRule("VOWEL-013","6.1.77","Yaṇ",("ḷ",),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"l","ḷ before a vowel is replaced by l",40),
    SandhiRule("VOWEL-014","6.1.78","Eco'yavāyāvaḥ",("e",),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"ay","e before a vowel is replaced by ay",50),
    SandhiRule("VOWEL-015","6.1.78","Eco'yavāyāvaḥ",("o",),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"av","o before a vowel is replaced by av",50),
    SandhiRule("VOWEL-016","6.1.78","Eco'yavāyāvaḥ",("ai",),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"āy","ai before a vowel is replaced by āy",50),
    SandhiRule("VOWEL-017","6.1.78","Eco'yavāyāvaḥ",("au",),("a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"),"āv","au before a vowel is replaced by āv",50),
]
VOWELS = sorted({v for r in RULES for v in r.left+r.right}, key=len, reverse=True)

def rule_catalog():
    return [asdict(r) for r in RULES]

def apply_boundary(left_word: str, right_word: str):
    """Apply one listed rule to the final/initial vowel boundary.

    Inputs should be IAST strings. The function returns every matching
    candidate in priority order because real grammatical context can matter.
    """
    if not left_word or not right_word:
        raise ValueError("Both boundary inputs must be non-empty.")
    matches=[]
    for r in RULES:
        for lv in sorted(r.left, key=len, reverse=True):
            for rv in sorted(r.right, key=len, reverse=True):
                if left_word.endswith(lv) and right_word.startswith(rv):
                    matches.append({
                        "rule_id":r.rule_id,"sutra":r.sutra,"name":r.name,
                        "result":left_word[:-len(lv)] + r.replacement + (right_word if r.rule_id in {
                            "VOWEL-010","VOWEL-011","VOWEL-012","VOWEL-013",
                            "VOWEL-014","VOWEL-015","VOWEL-016","VOWEL-017"
                        } else right_word[len(rv):]),
                        "boundary":lv + " + " + rv,
                        "explanation":r.explanation
                    })
    matches.sort(key=lambda x: (next(r.priority for r in RULES if r.rule_id==x["rule_id"]),x["rule_id"]))
    # De-duplicate same rule/output when vowel alternatives overlap.
    unique=[]; seen=set()
    for m in matches:
        key=(m["rule_id"],m["result"])
        if key not in seen: unique.append(m); seen.add(key)
    return unique

def reverse_candidates(surface: str):
    """Enumerate possible splits by reversing listed replacement strings.

    This is intentionally ambiguous and does not claim unique morphological
    or grammatical reconstruction.
    """
    found=[]
    for r in RULES:
        for lv in r.left:
            for rv in r.right:
                # Reverse a boundary replacement occurring at any location.
                start=0
                while True:
                    idx=surface.find(r.replacement, start)
                    if idx < 0: break
                    left_stem=surface[:idx]
                    right_stem=surface[idx+len(r.replacement):]
                    candidate={"rule_id":r.rule_id,"sutra":r.sutra,"name":r.name,
                               "left":left_stem+lv,"right":rv+right_stem,
                               "surface":surface,"explanation":r.explanation}
                    if candidate not in found: found.append(candidate)
                    start=idx+1
    return found

def explain_coordinate_profile():
    return {
      "profile":"PLC-CODEBOOK-2",
      "dimensions":[
        {"index":0,"name":"place","meaning":"Broad place-of-articulation category","type":"categorical integer"},
        {"index":1,"name":"manner","meaning":"Broad manner-of-articulation category","type":"categorical integer"},
        {"index":2,"name":"voicing","meaning":"Starter binary voicing feature","type":"0/1"},
        {"index":3,"name":"phoneme_class","meaning":"Starter vowel/consonant/other class","type":"categorical integer"},
        {"index":4,"name":"bhava_slot","meaning":"Reserved user-defined Bhāva slot; currently zero","type":"integer"},
        {"index":5,"name":"token_id","meaning":"Stable reversible codebook index","type":"integer"}
      ],
      "separate_conceptual_axes":{"X":"Bhūta","Y":"Rasa","Z":"Kāla","W":"Varṇa cluster"},
      "warning":"These are explicit software conventions, not a recovered traditional coordinate system or a cryptographic primitive."
    }
