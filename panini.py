"""Small, explicit Śiva-sūtra / pratyāhāra reference engine.

This implements the standard 14 Śiva-sūtra sequence and the classical
start-varṇa + it-marker range operation. It is a reference helper, not a
complete Pāṇinian grammar or Aṣṭādhyāyī interpreter.
"""
SUTRAS = [
    ("a i u", "ṇ"),
    ("ṛ ḷ", "k"),
    ("e o", "ṅ"),
    ("ai au", "c"),
    ("h y v r", "ṭ"),
    ("l", "ṇ"),
    ("ñ m ṅ ṇ n", "m"),
    ("jh bh", "ñ"),
    ("gh ḍh dh", "ṣ"),
    ("j b g ḍ d", "ś"),
    ("kh ph ch ṭh th c ṭ t", "v"),
    ("k p", "y"),
    ("ś ṣ s", "r"),
    ("h", "l"),
]
# Ordered sequence of phonemes and markers as they occur in the Śiva Sūtras.
SEQUENCE = []
for body, marker in SUTRAS:
    SEQUENCE.extend(body.split())
    SEQUENCE.append("{" + marker + "}")

MARKERS = [marker for _, marker in SUTRAS]
STARTS = sorted({x for body, _ in SUTRAS for x in body.split()})

def sutra_rows():
    return [{"number":i+1, "phonemes":body.split(), "it_marker":marker}
            for i,(body,marker) in enumerate(SUTRAS)]

def pratyahara(start_varna: str, ending_marker: str, start_occurrence: int = 0,
               marker_occurrence: int = 0) -> list[str]:
    """Return phonemes from chosen start occurrence up to chosen it-marker.

    Occurrence indices are zero-based among matching start varṇas/markers.
    The ending marker itself is excluded from the returned phoneme set.
    """
    starts = [i for i,x in enumerate(SEQUENCE) if x == start_varna]
    ends = [i for i,x in enumerate(SEQUENCE) if x == "{" + ending_marker + "}"]
    if not starts:
        raise ValueError(f"Unknown start varṇa: {start_varna}")
    if not ends:
        raise ValueError(f"Unknown it-marker: {ending_marker}")
    if start_occurrence >= len(starts) or marker_occurrence >= len(ends):
        raise ValueError("Requested occurrence does not exist.")
    si, ei = starts[start_occurrence], ends[marker_occurrence]
    if ei <= si:
        raise ValueError("The selected ending marker must occur after the selected start varṇa.")
    return [x for x in SEQUENCE[si:ei] if not x.startswith("{")]

def occurrences():
    from collections import Counter
    return {
        "starts": {x: sum(1 for y in SEQUENCE if y == x) for x in STARTS},
        "markers": {x: MARKERS.count(x) for x in sorted(set(MARKERS))}
    }