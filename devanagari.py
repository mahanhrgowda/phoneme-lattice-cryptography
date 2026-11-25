"""Practical Devanagari-to-IAST transliteration for common Sanskrit orthography.

This is a lightweight orthographic transliterator, not a Sanskrit sandhi,
morphology, Vedic accent, or full Unicode-script normalization engine.
"""
import unicodedata

INDEPENDENT = {
    "अ":"a","आ":"ā","इ":"i","ई":"ī","उ":"u","ऊ":"ū",
    "ऋ":"ṛ","ॠ":"ṝ","ऌ":"ḷ","ॡ":"ḹ","ए":"e","ऐ":"ai","ओ":"o","औ":"au",
}
CONSONANTS = {
    "क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"ṅ",
    "च":"c","छ":"ch","ज":"j","झ":"jh","ञ":"ñ",
    "ट":"ṭ","ठ":"ṭh","ड":"ḍ","ढ":"ḍh","ण":"ṇ",
    "त":"t","थ":"th","द":"d","ध":"dh","न":"n",
    "प":"p","फ":"ph","ब":"b","भ":"bh","म":"m",
    "य":"y","र":"r","ल":"l","व":"v",
    "श":"ś","ष":"ṣ","स":"s","ह":"h",
    "ळ":"ḷ",
}
MATRA = {
    "ा":"ā","ि":"i","ी":"ī","ु":"u","ू":"ū","ृ":"ṛ","ॄ":"ṝ",
    "ॢ":"ḷ","ॣ":"ḹ","े":"e","ै":"ai","ो":"o","ौ":"au",
}
SIGNS = {"ं":"ṃ","ः":"ḥ","ँ":"m̐","ऽ":"'","ॐ":"oṃ"}
VIRAMA = "्"
NUKTA = "़"
NUKTA_MAP = {
    ("क","़"):"q", ("ख","़"):"x", ("ग","़"):"ġ",
    ("ज","़"):"z", ("ड","़"):"ṛ", ("ढ","़"):"ṛh",
    ("फ","़"):"f", ("य","़"):"ẏ",
}
DIGITS = dict(zip("०१२३४५६७८९","0123456789"))

def transliterate(text: str) -> str:
    s = unicodedata.normalize("NFC", text)
    out=[]
    i=0
    while i < len(s):
        ch=s[i]
        if ch in SIGNS:
            out.append(SIGNS[ch]); i+=1; continue
        if ch in INDEPENDENT:
            out.append(INDEPENDENT[ch]); i+=1; continue
        if ch in CONSONANTS:
            base=CONSONANTS[ch]
            if i+1 < len(s) and s[i+1] == NUKTA:
                base=NUKTA_MAP.get((ch,NUKTA),base)
                i+=1
            i+=1
            if i < len(s) and s[i] == VIRAMA:
                out.append(base); i+=1
            elif i < len(s) and s[i] in MATRA:
                out.append(base + MATRA[s[i]]); i+=1
            else:
                out.append(base + "a")
            continue
        if ch in MATRA:
            # Orphan matra: preserve rather than silently discard.
            out.append(ch); i+=1; continue
        if ch in DIGITS:
            out.append(DIGITS[ch]); i+=1; continue
        if ch in ("।","॥"):
            out.append(" | " if ch=="।" else " || "); i+=1; continue
        out.append(ch); i+=1
    return "".join(out)
