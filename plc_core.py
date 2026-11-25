"""Deterministic, reversible PLC lattice core.

The codebook is a documented starter convention, not a recovered historical
Maheshwara coordinate table. The final coordinate component is a stable token
ID, making every codebook token uniquely decodable.
"""
from __future__ import annotations
import json
import unicodedata
from typing import Any

PROFILE = "PLC-CODEBOOK-2"
PLACES = {
    "bilabial": 0, "labiodental": 1, "dental": 2, "alveolar": 3,
    "retroflex": 4, "palatal": 5, "velar": 6, "glottal": 7,
    "vowel": 8, "other": 9,
}
MANNERS = {
    "stop": 0, "nasal": 1, "fricative": 2, "affricate": 3,
    "approximant": 4, "lateral": 5, "vowel": 6, "other": 7,
}

# Token inventory uses longest-match IAST units. Token IDs are stable within
# this profile; adding/reordering tokens requires a new profile version.
TOKENS = [
    "kṣ","jñ","kh","gh","ch","jh","ṭh","ḍh","th","dh","ph","bh",
    "ṅ","ñ","ṭ","ḍ","ṇ","ś","ṣ","ṃ","ḥ","m̐",
    "ā","ī","ū","ṛ","ṝ","ḷ","ḹ","ai","au",
    "a","i","u","e","o","k","g","c","j","t","d","n","p","b","m",
    "y","r","l","v","s","h",
]
# Articulatory feature labels are an explicit starter approximation.
FEATURES: dict[str, tuple[int,int,int,int]] = {}
def _set(tokens: str, place: str, manner: str, voiced: int):
    for token in tokens.split():
        FEATURES[token] = (PLACES[place], MANNERS[manner], voiced, 0)

_set("p ph", "bilabial", "stop", 0)
_set("b bh", "bilabial", "stop", 1)
_set("m", "bilabial", "nasal", 1)
_set("t th", "dental", "stop", 0)
_set("d dh", "dental", "stop", 1)
_set("n", "dental", "nasal", 1)
_set("ṭ ṭh", "retroflex", "stop", 0)
_set("ḍ ḍh", "retroflex", "stop", 1)
_set("ṇ", "retroflex", "nasal", 1)
_set("k kh", "velar", "stop", 0)
_set("g gh", "velar", "stop", 1)
_set("ṅ", "velar", "nasal", 1)
_set("c ch", "palatal", "affricate", 0)
_set("j jh", "palatal", "affricate", 1)
_set("ñ", "palatal", "nasal", 1)
_set("ś", "palatal", "fricative", 0)
_set("ṣ", "retroflex", "fricative", 0)
_set("s", "alveolar", "fricative", 0)
_set("y", "palatal", "approximant", 1)
_set("r", "alveolar", "approximant", 1)
_set("l", "alveolar", "lateral", 1)
_set("v", "labiodental", "approximant", 1)
_set("h", "glottal", "fricative", 0)
_set("a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au", "vowel", "vowel", 1)
_set("ṃ m̐", "other", "nasal", 1)
_set("ḥ", "glottal", "fricative", 0)

TOKEN_TO_ID = {t: i for i, t in enumerate(TOKENS)}
ID_TO_TOKEN = {i: t for t, i in TOKEN_TO_ID.items()}
MAX_MATCH = max(map(len, TOKENS))

def tokenize_iast(text: str) -> list[str]:
    """Longest-match tokenizer; preserves spaces, punctuation and unknown chars."""
    s = unicodedata.normalize("NFC", text)
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i].isspace() or not s[i].isalpha():
            out.append(s[i])
            i += 1
            continue
        match = next((t for t in TOKENS if s.startswith(t, i)), None)
        if match:
            out.append(match)
            i += len(match)
        else:
            # Unknown characters are preserved as literal tokens.
            out.append(s[i])
            i += 1
    return out

def coordinate_for(token: str) -> list[int]:
    """Six-dimensional stable coordinate: place,manner,voicing,class,bhava,token_id."""
    token_id = TOKEN_TO_ID.get(token)
    if token_id is None:
        # Unknown literals use a disjoint Unicode codepoint range.
        if len(token) != 1:
            raise ValueError(f"Unknown token must be a single character: {token!r}")
        token_id = 1000 + ord(token)
        features = (PLACES["other"], MANNERS["other"], 0, 2)
    else:
        features = FEATURES.get(token, (PLACES["other"], MANNERS["other"], 0, 2))
        is_vowel = int(features[1] == MANNERS["vowel"])
        features = (features[0], features[1], features[2], is_vowel)
    return [features[0], features[1], features[2], features[3], 0, token_id]

def encode(text: str) -> dict[str, Any]:
    tokens = tokenize_iast(text)
    records = [{"token": t, "coordinate": coordinate_for(t)} for t in tokens]
    return {
        "format": PROFILE,
        "dimensions": ["place", "manner", "voicing", "phoneme_class", "bhava_slot", "token_id"],
        "profile_note": "Starter articulatory codebook; not a recovered historical coordinate map.",
        "source_text_normalization": "Unicode NFC",
        "records": records,
    }

def decode(payload: dict[str, Any]) -> str:
    if payload.get("format") != PROFILE:
        raise ValueError(f"Unsupported profile. Expected {PROFILE}.")
    parts = []
    for record in payload.get("records", []):
        token = record.get("token")
        coord = record.get("coordinate")
        if not isinstance(token, str) or not isinstance(coord, list) or len(coord) != 6:
            raise ValueError("Malformed lattice record.")
        expected = coordinate_for(token)
        if coord != expected:
            raise ValueError(f"Coordinate/token mismatch for {token!r}.")
        parts.append(token)
    return "".join(parts)

def validate_codebook() -> dict[str, Any]:
    coords = {t: tuple(coordinate_for(t)) for t in TOKENS}
    reverse: dict[tuple[int,...], list[str]] = {}
    for token, coord in coords.items():
        reverse.setdefault(coord, []).append(token)
    collisions = {str(k): v for k, v in reverse.items() if len(v) > 1}
    return {
        "profile": PROFILE,
        "token_count": len(TOKENS),
        "unique_coordinate_count": len(set(coords.values())),
        "collision_count": len(collisions),
        "collisions": collisions,
        "reversible": not collisions,
    }

def export_codebook_csv() -> str:
    lines = ["token,token_id,place,manner,voicing,phoneme_class,bhava_slot"]
    for token in TOKENS:
        c = coordinate_for(token)
        lines.append(",".join([json.dumps(token, ensure_ascii=False), str(c[5]), *map(str, c[:5])]))
    return "\n".join(lines) + "\n"
