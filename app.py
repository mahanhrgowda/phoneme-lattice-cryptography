import base64
import hashlib
import time
import hmac
import json
import re
import secrets
import string
from typing import Dict, List, Tuple

import streamlit as st
import plc_core
import devanagari
import sandhi
import bhava_vectors
import trishula_lab
import panini_engine
import qrcode
from io import BytesIO
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

st.set_page_config(page_title="PLC Studio", page_icon="🔐", layout="wide")
st.title("🔐 Phoneme Lattice Cryptography Studio")
st.caption("Maheshwara-inspired phonology • Reversible lattice encoding • Authenticated encryption")
st.caption("PLC Studio 3.0 — Pāṇinian phonological engine research release")

# This is an explicit, reproducible starter profile, not a claim that these
# coordinates were present in the user's original historical prototype.
PROFILE_NOTE = (
    "Starter feature profile: coordinates are generated from documented "
    "phonological feature tables. They are reversible through the token table, "
    "but are not a recovered historical coordinate dictionary."
)

# Broad articulatory categories. Values are compact categorical indices.
PLACE = {
    "bilabial": 0, "labiodental": 1, "dental": 2, "alveolar": 3,
    "retroflex": 4, "palatal": 5, "velar": 6, "glottal": 7,
    "vowel": 8, "other": 9
}
MANNER = {
    "stop": 0, "nasal": 1, "fricative": 2, "affricate": 3,
    "approximant": 4, "lateral": 5, "vowel": 6, "other": 7
}
# A compact starter inventory; extend through the Mapping editor.
PHONEMES = {
    # Sanskrit/IAST consonants
    "क":"k", "ख":"kh", "ग":"g", "घ":"gh", "ङ":"ṅ",
    "च":"c", "छ":"ch", "ज":"j", "झ":"jh", "ञ":"ñ",
    "ट":"ṭ", "ठ":"ṭh", "ड":"ḍ", "ढ":"ḍh", "ण":"ṇ",
    "त":"t", "थ":"th", "द":"d", "ध":"dh", "न":"n",
    "प":"p", "फ":"ph", "ब":"b", "भ":"bh", "म":"m",
    "य":"y", "र":"r", "ल":"l", "व":"v",
    "श":"ś", "ष":"ṣ", "स":"s", "ह":"h",
    "क्ष":"kṣ", "ज्ञ":"jñ",
    # IAST vowels and common signs
    "अ":"a", "आ":"ā", "इ":"i", "ई":"ī", "उ":"u", "ऊ":"ū",
    "ऋ":"ṛ", "ॠ":"ṝ", "ए":"e", "ऐ":"ai", "ओ":"o", "औ":"au",
    "ं":"ṃ", "ः":"ḥ", "ँ":"m̐",
}
# IAST token inventory. Longest-match tokenization avoids splitting aspirates.
IAST_TOKENS = sorted([
    "kṣ","jñ","kh","gh","ch","jh","ṭh","ḍh","th","dh","ph","bh",
    "ṅ","ñ","ṭ","ḍ","ṇ","ś","ṣ","ṃ","ḥ","m̐",
    "ā","ī","ū","ṛ","ṝ","ḷ","ḹ","ai","au","a","i","u","e","o",
    "k","g","c","j","t","d","n","p","b","m","y","r","l","v","s","h"
], key=len, reverse=True)

# Approximate feature labels for a starter phoneme inventory.
FEATURES = {}
def add_group(tokens, place, manner, voiced):
    for token in tokens.split():
        FEATURES[token] = (PLACE[place], MANNER[manner], int(voiced), 0)

add_group("p ph b bh m", "bilabial", "stop", False)
for t in ["b","bh","m"]: FEATURES[t] = (PLACE["bilabial"], MANNER["nasal"] if t=="m" else MANNER["stop"], 1, 0)
add_group("t th d dh n", "dental", "stop", False)
for t in ["d","dh","n"]: FEATURES[t] = (PLACE["dental"], MANNER["nasal"] if t=="n" else MANNER["stop"], 1, 0)
add_group("ṭ ṭh ḍ ḍh ṇ", "retroflex", "stop", False)
for t in ["ḍ","ḍh","ṇ"]: FEATURES[t] = (PLACE["retroflex"], MANNER["nasal"] if t=="ṇ" else MANNER["stop"], 1, 0)
add_group("k kh g gh ṅ", "velar", "stop", False)
for t in ["g","gh","ṅ"]: FEATURES[t] = (PLACE["velar"], MANNER["nasal"] if t=="ṅ" else MANNER["stop"], 1, 0)
add_group("c ch j jh ñ", "palatal", "affricate", False)
for t in ["j","jh","ñ"]: FEATURES[t] = (PLACE["palatal"], MANNER["nasal"] if t=="ñ" else MANNER["affricate"], 1, 0)
for t in ["ś","ṣ","s"]: FEATURES[t] = (PLACE["palatal"] if t=="ś" else PLACE["retroflex"] if t=="ṣ" else PLACE["alveolar"], MANNER["fricative"], 0, 0)
for t in ["y","r","l","v"]: FEATURES[t] = (PLACE["palatal"] if t=="y" else PLACE["alveolar"], MANNER["approximant"] if t!="l" else MANNER["lateral"], 1, 0)
FEATURES["h"] = (PLACE["glottal"], MANNER["fricative"], 0, 0)
for t in ["a","ā","i","ī","u","ū","ṛ","ṝ","e","ai","o","au"]:
    FEATURES[t] = (PLACE["vowel"], MANNER["vowel"], 1, 0)
FEATURES["ṃ"] = (PLACE["other"], MANNER["nasal"], 1, 0)
FEATURES["ḥ"] = (PLACE["glottal"], MANNER["fricative"], 0, 0)
FEATURES["m̐"] = (PLACE["other"], MANNER["nasal"], 1, 0)

def tokenize_iast(text: str) -> List[str]:
    return plc_core.tokenize_iast(text)

def token_feature(token: str, position: int) -> List[int]:
    return plc_core.coordinate_for(token)

def lattice_encode(text: str, mode: str) -> dict:
    if mode == "Literal characters":
        # A literal mode is still represented reversibly, one Unicode character per token.
        records = [{"token": ch, "coordinate": plc_core.coordinate_for(ch)}
                   for ch in text]
        coords = [tuple(r["coordinate"]) for r in records]
        if len(coords) != len(set(coords)):
            # Repeated literal characters are valid; position is added as a seventh dimension.
            records = [{"token": ch, "coordinate": plc_core.coordinate_for(ch) + [i]}
                       for i, ch in enumerate(text)]
        return {"format":"PLC-LATTICE-LITERAL-2", "dimensions":["place","manner","voicing","phoneme_class","bhava_slot","token_id","position"], "records":records}
    return plc_core.encode(text)

def lattice_decode(obj: dict) -> str:
    if obj.get("format") == "PLC-LATTICE-LITERAL-2":
        return "".join(row["token"] for row in obj["records"])
    if obj.get("format") == plc_core.PROFILE:
        return plc_core.decode(obj)
    raise ValueError("Unsupported lattice format.")

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))

def encrypt_payload(plaintext: str, password: str, include_lattice: bool, mode: str) -> str:
    if not password:
        raise ValueError("Enter a passphrase.")
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    key = derive_key(password, salt)
    content = {"plaintext": plaintext, "version": 1}
    if include_lattice:
        content["lattice"] = lattice_encode(plaintext, mode)
    raw = json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, raw, b"PLC-STUDIO-v1")
    envelope = {
        "format": "PLC-AESGCM-1",
        "kdf": {"name": "scrypt", "n": 16384, "r": 8, "p": 1, "salt": base64.b64encode(salt).decode()},
        "cipher": {"name": "AES-256-GCM", "nonce": base64.b64encode(nonce).decode()},
        "ciphertext": base64.b64encode(ciphertext).decode()
    }
    return base64.b64encode(json.dumps(envelope, separators=(",", ":")).encode()).decode()

def decrypt_payload(payload: str, password: str) -> dict:
    try:
        envelope = json.loads(base64.b64decode(payload.strip()))
        if envelope.get("format") != "PLC-AESGCM-1":
            raise ValueError("Not a PLC AES-GCM payload.")
        salt = base64.b64decode(envelope["kdf"]["salt"])
        nonce = base64.b64decode(envelope["cipher"]["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        key = derive_key(password, salt)
        raw = AESGCM(key).decrypt(nonce, ciphertext, b"PLC-STUDIO-v1")
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Decryption failed. Check the payload and passphrase; the data may have been modified.") from exc

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def hmac_hex(text: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()

def mapping_csv_template():
    return "token,place,manner,voicing,phoneme_class,bhava_slot\nk,6,0,0,0,0\nm,0,1,1,0,0\na,8,6,1,1,0\n"


MAHESHWARA_SUTRAS = [
    ("अइउण्", "a i u ṇ", "Vowels a, i, u; marker ṇ"),
    ("ऋऌक्", "ṛ ḷ k", "Vocalic ṛ and ḷ; marker k"),
    ("एओङ्", "e o ṅ", "e and o; marker ṅ"),
    ("ऐऔच्", "ai au c", "ai and au; marker c"),
    ("हयवरट्", "ha ya va ra ṭ", "ha, ya, va, ra; marker ṭ"),
    ("लण्", "la ṇ", "la; marker ṇ"),
    ("ञमङणनम्", "ña ma ṅa ṇa na m", "Nasals; marker m"),
    ("झभञ्", "jha bha ñ", "jha, bha; marker ñ"),
    ("घढधष्", "gha ḍha dha ṣ", "gha, ḍha, dha; marker ṣ"),
    ("जबगडदश्", "ja ba ga ḍa da ś", "ja, ba, ga, ḍa, da; marker ś"),
    ("खफछठथचटतव्", "kha pha cha ṭha tha ca ṭa ta v", "Aspirates and stops; marker v"),
    ("कपय्", "ka pa y", "ka, pa; marker y"),
    ("शषसर्", "śa ṣa sa r", "Sibilants; marker r"),
    ("हल्", "ha l", "Consonant pratyāhāra terminator; marker l"),
]
BHAVAS = [
    "Śāntiḥ","Ānandaḥ","Bhaktiḥ","Jñānam","Karunā","Āstikyam",
    "Vīryam","Utsāhaḥ","Rāgaḥ","Dainyaḥ","Harṣaḥ","Īrṣyā",
    "Krodhaḥ","Bhayam","Vairāgyam","Mādhuryam","Dhṛtiḥ",
    "Nirvedaḥ","Ākrośaḥ","Āścaryaṁ","Mohaḥ","Lajjā"
]

def make_lwe_keypair(n=16, m=32, q=32768):
    # Educational Regev-style LWE toy construction. These tiny parameters
    # are intentionally unsuitable for real-world security.
    A = [[secrets.randbelow(q) for _ in range(n)] for _ in range(m)]
    secret = [secrets.randbelow(3)-1 for _ in range(n)]
    error = [secrets.randbelow(3)-1 for _ in range(m)]
    b = [(sum(A[i][j]*secret[j] for j in range(n)) + error[i]) % q for i in range(m)]
    return {"A": A, "b": b, "n": n, "m": m, "q": q}, secret

def lwe_encrypt_bytes(data: bytes, public: dict) -> dict:
    A, b, n, m, q = public["A"], public["b"], public["n"], public["m"], public["q"]
    bits = [((byte >> shift) & 1) for byte in data for shift in range(7, -1, -1)]
    encrypted = []
    for bit in bits:
        chosen = [i for i in range(m) if secrets.randbelow(2)]
        u = [sum(A[i][j] for i in chosen) % q for j in range(n)]
        v = (sum(b[i] for i in chosen) + bit*(q//2)) % q
        encrypted.append({"u": u, "v": v})
    return {"format":"PLC-TOY-LWE-1", "n":n, "m":m, "q":q, "bits":encrypted}

def lwe_decrypt_bytes(cipher: dict, secret: list) -> bytes:
    q = cipher["q"]
    bits = []
    for item in cipher["bits"]:
        phase = (item["v"] - sum(secret[j]*item["u"][j] for j in range(len(secret)))) % q
        bits.append(1 if q//4 < phase < 3*q//4 else 0)
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) != 8:
            raise ValueError("Ciphertext bit count is not byte-aligned.")
        value = 0
        for bit in chunk:
            value = (value << 1) | bit
        out.append(value)
    return bytes(out)


tabs = st.tabs(["Encrypt", "Decrypt", "Lattice Lab", "Sūtra & Bhāva", "Toy LWE Lab", "Hash", "Batch", "Mapping & Notes", "Sandhi Lab", "Bhāva Vectors", "Trishula Lab", "Benchmarks", "Pāṇini Engine"])

with tabs[0]:
    st.subheader("Authenticated encryption")
    left, right = st.columns([3, 2])
    with left:
        plain = st.text_area("Plaintext", height=180, placeholder="Enter text to encrypt…")
        mode = st.selectbox("Lattice tokenizer", ["IAST (Sanskrit transliteration)", "Literal characters"])
        add_lattice = st.checkbox("Embed lattice representation inside encrypted payload", value=True)
    with right:
        password = st.text_input("Passphrase", type="password", key="enc_pw")
        st.caption("Use a long, unique passphrase. The app does not store it.")
        st.info("AES-256-GCM + Scrypt key derivation. Each encryption uses a fresh random salt and nonce.")
    if st.button("Encrypt", type="primary", disabled=not plain or not password):
        try:
            result = encrypt_payload(plain, password, add_lattice, mode)
            st.success("Encrypted successfully.")
            st.text_area("PLC encrypted payload (Base64 envelope)", result, height=150)
            st.download_button("Download encrypted payload", result, file_name="plc_encrypted.txt")
            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=7, border=4)
            qr.add_data(result)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            qr_buf = BytesIO()
            qr_img.save(qr_buf, format="PNG")
            st.image(qr_img, caption="QR code containing the encrypted payload", width=300)
            st.download_button("Download encrypted QR (PNG)", qr_buf.getvalue(), "plc_encrypted_qr.png", "image/png")
        except Exception as e:
            st.error(str(e))

with tabs[1]:
    st.subheader("Decrypt PLC payload")
    st.markdown("Upload the encrypted QR image generated by PLC Studio, or paste the Base64 payload directly.")
    qr_upload = st.file_uploader(
        "Upload encrypted QR code image",
        type=["png", "jpg", "jpeg", "webp"],
        key="decrypt_qr_upload",
        help="The QR code should contain the PLC encrypted Base64 envelope."
    )
    qr_payload = ""
    if qr_upload is not None:
        try:
            import cv2
            import numpy as np
            from PIL import Image

            image = Image.open(qr_upload).convert("RGB")
            image_array = np.array(image)
            detector = cv2.QRCodeDetector()
            qr_payload, points, _ = detector.detectAndDecode(image_array)
            if qr_payload:
                st.success("QR code detected. Its encrypted payload is ready to decrypt.")
                st.caption("The uploaded QR payload will be used for decryption.")
                with st.expander("View decoded QR payload"):
                    st.code(qr_payload, language=None)
            else:
                st.error("No readable QR code was found in this image. Try a clearer PNG/JPG image or paste the payload below.")
        except ImportError:
            st.error("QR image decoding requires OpenCV. Install the dependency with: pip install opencv-python-headless")
        except Exception as e:
            st.error(f"Could not read the QR image: {e}")

    pasted_payload = st.text_area("Or paste encrypted PLC payload", height=160, key="decrypt_payload_text")
    payload = qr_payload or pasted_payload.strip()
    if qr_payload and pasted_payload.strip():
        st.info("Using the payload decoded from the uploaded QR image.")
    dec_pw = st.text_input("Passphrase", type="password", key="dec_pw")
    if st.button("Decrypt", type="primary", disabled=not payload or not dec_pw):
        try:
            recovered = decrypt_payload(payload, dec_pw)
            st.success("Authentication passed; plaintext recovered.")
            st.text_area("Recovered plaintext", recovered["plaintext"], height=150)
            if "lattice" in recovered:
                with st.expander("Embedded lattice payload"):
                    st.json(recovered["lattice"])
        except ValueError as e:
            st.error(str(e))

with tabs[2]:
    st.subheader("Phoneme lattice laboratory")
    lab_text = st.text_area("Text to represent", "maheshwara", key="lab_text")
    lab_mode = st.selectbox("Tokenization mode", ["IAST (Sanskrit transliteration)", "Literal characters"], key="lab_mode")
    if st.button("Generate lattice"):
        obj = lattice_encode(lab_text, lab_mode)
        st.json(obj)
        st.download_button("Download lattice JSON", json.dumps(obj, ensure_ascii=False, indent=2),
                           file_name="plc_lattice.json", mime="application/json")
    st.divider()
    st.markdown("**Devanagari → IAST → lattice**")
    devan_text = st.text_area("Enter Sanskrit in Devanagari", "नमः शिवाय", key="dev_input")
    if st.button("Transliterate and encode Devanagari"):
        iast_text = devanagari.transliterate(devan_text)
        st.text_input("IAST output", iast_text)
        dev_lattice = plc_core.encode(iast_text)
        st.json(dev_lattice)
        st.download_button("Download Devanagari-derived lattice", json.dumps(dev_lattice, ensure_ascii=False, indent=2),
                           "plc_devanagari_lattice.json", "application/json")
    st.caption("Orthographic transliteration supports common Sanskrit Devanagari. It does not infer sandhi, grammar, Vedic accents or missing vowel/consonant distinctions.")
    st.markdown("**Configurable lattice projections**")
    proj_text = st.text_input("Text for projection", "maheshwara", key="projection_text")
    projection = st.selectbox("Projection dimensions", ["3D", "4D", "6D", "7D"], key="projection_dims")
    if st.button("Build projection"):
        encoded = plc_core.encode(proj_text)
        rows = []
        for idx, rec in enumerate(encoded["records"]):
            c = rec["coordinate"]
            row = {"token":rec["token"], "X_place":c[0], "Y_manner":c[1], "Z_voicing":c[2],
                   "W_class":c[3], "V_bhava_slot":c[4], "U_token_id":c[5], "T_position":idx}
            rows.append(row)
        cols = {
            "3D":["token","X_place","Y_manner","Z_voicing"],
            "4D":["token","X_place","Y_manner","Z_voicing","W_class"],
            "6D":["token","X_place","Y_manner","Z_voicing","W_class","V_bhava_slot","U_token_id"],
            "7D":["token","X_place","Y_manner","Z_voicing","W_class","V_bhava_slot","U_token_id","T_position"]
        }[projection]
        import pandas as pd
        frame = pd.DataFrame(rows, columns=cols)
        st.dataframe(frame, use_container_width=True)
        st.download_button("Download projection CSV", frame.to_csv(index=False), "plc_lattice_projection.csv", "text/csv")
        st.caption("These are engineering projections of the starter articulatory codebook. They are not the same as the conceptual Bhūta–Rasa–Kāla–Varṇa axes.")
        st.markdown("**Decode a lattice JSON file**")
    up = st.file_uploader("Upload PLC-LATTICE-1 JSON", type=["json"])
    if up:
        try:
            decoded = lattice_decode(json.load(up))
            st.text_area("Decoded token stream", decoded, height=100)
        except Exception as e:
            st.error(f"Could not decode: {e}")
    st.warning(PROFILE_NOTE)
    st.divider()
    st.markdown("**Canonical codebook validation**")
    report = plc_core.validate_codebook()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tokens", report["token_count"])
    c2.metric("Unique coordinates", report["unique_coordinate_count"])
    c3.metric("Collisions", report["collision_count"])
    if report["reversible"]:
        st.success("Every registered phoneme has a unique stable coordinate.")
    else:
        st.error("Codebook collisions detected.")
    st.download_button("Export canonical codebook CSV", plc_core.export_codebook_csv(),
                       "plc_canonical_codebook_v2.csv", "text/csv")
    st.caption("The final coordinate is a stable codebook token ID. It guarantees invertibility but is an engineering index, not a claim about ancient Sanskrit phonetic numerology.")


with tabs[3]:
    st.subheader("Maheshwara Sūtra and Bhāva explorer")
    st.markdown("The 14 traditional Śiva Sūtras are presented as phonological groupings with their it-markers. This is a reference view, not a full Pāṇinian pratyāhāra parser.")
    for idx, (dev, translit, note) in enumerate(MAHESHWARA_SUTRAS, 1):
        with st.expander(f"{idx:02d}. {dev}  —  {translit}"):
            st.write(note)
    st.divider()
    st.markdown("**Your 22-Bhāva catalogue**")
    chosen_bhava = st.selectbox("Select a Bhāva", BHAVAS)
    st.write(f"Selected Bhāva: **{chosen_bhava}**")
    st.caption("Bhāva labels are preserved from your research. Numerical Bhāva weights and phoneme-to-Bhāva correspondences remain user-defined; this release does not fabricate them.")
    st.download_button("Export 22-Bhāva catalogue (CSV)",
        "index,bhava\n" + "\n".join(f"{i+1},{b}" for i,b in enumerate(BHAVAS)),
        "plc_22_bhavas.csv", "text/csv")
    st.divider()
    st.markdown("**Your original 4D Maheshwara Lattice axes**")
    st.code("X = Bhūta\\nY = Rasa\\nZ = Kāla\\nW = Varṇa cluster")
    st.caption("Conceptual semantic axes are retained separately from the articulatory coordinate projections in the Lattice Lab.")
    st.caption("Earlier English PLC proposal: X = phoneme class, Y = articulation place, Z = voicing/energy; semantic Bhāva or stress/intonation was proposed as a 4th dimension.")

with tabs[4]:
    st.subheader("Experimental LWE laboratory")
    st.warning("Research demonstration only — NOT secure cryptography. Tiny parameters, unreviewed implementation, and no side-channel protections. Use AES-GCM above for actual confidentiality.")
    st.markdown("This tab demonstrates the core LWE idea: a public noisy linear relation **b = A·s + e (mod q)**, where recovering secret vector **s** should be difficult only with appropriately chosen, rigorously analyzed parameters. The tiny parameters here are deliberately insecure.")
    demo_text = st.text_area("Short message for toy LWE encryption", "PLC research", key="lwe_text", max_chars=64)
    if st.button("Generate toy LWE keypair and encrypt"):
        pub, sec = make_lwe_keypair()
        cipher = lwe_encrypt_bytes(demo_text.encode("utf-8"), pub)
        st.session_state["lwe_demo"] = {"public":pub, "secret":sec, "cipher":cipher}
        st.success("Toy keypair and ciphertext generated in this session.")
    if "lwe_demo" in st.session_state:
        demo = st.session_state["lwe_demo"]
        st.write("Public key dimensions:", f"A = {demo['public']['m']} × {demo['public']['n']}, q = {demo['public']['q']}")
        st.json({"ciphertext_format":demo["cipher"]["format"], "encrypted_bits":len(demo["cipher"]["bits"]), "example_first_bit":demo["cipher"]["bits"][0] if demo["cipher"]["bits"] else None})
        if st.button("Decrypt toy LWE ciphertext"):
            try:
                recovered = lwe_decrypt_bytes(demo["cipher"], demo["secret"]).decode("utf-8")
                st.success("Toy decryption output: " + recovered)
            except Exception as exc:
                st.error(f"Toy decryption failed: {exc}")
        pub_json = json.dumps(demo["public"], separators=(",", ":"))
        cipher_json = json.dumps(demo["cipher"], separators=(",", ":"))
        st.download_button("Download public key JSON", pub_json, "plc_toy_lwe_public_key.json", "application/json")
        st.download_button("Download ciphertext JSON", cipher_json, "plc_toy_lwe_ciphertext.json", "application/json")
    st.caption("This is a pedagogical LWE prototype, not Ring-LWE, not ML-KEM, and not a drop-in replacement for a standardized post-quantum scheme.")

with tabs[5]:
    st.subheader("Maheshwara Hash workbench")
    hash_text = st.text_area("Input text", key="hash_text")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Generate SHA-256"):
            st.code(sha256_hex(hash_text))
    with c2:
        hkey = st.text_input("HMAC secret", type="password")
        if st.button("Generate HMAC-SHA256", disabled=not hkey):
            st.code(hmac_hex(hash_text, hkey))
    st.divider()
    st.markdown("**Experimental SHA3-512 profile**")
    if st.button("Generate SHA3-512"):
        st.code(hashlib.sha3_512(hash_text.encode("utf-8")).hexdigest())
    hkey3 = st.text_input("SHA3-512 HMAC secret", type="password", key="hmac3_key")
    if st.button("Generate HMAC-SHA3-512", disabled=not hkey3):
        st.code(hmac.new(hkey3.encode("utf-8"), hash_text.encode("utf-8"), hashlib.sha3_512).hexdigest())
    st.caption("SHA-256 and SHA3-512 are digests, not encryption. HMAC authenticates data when the secret key remains private. The SHA3-512 option is an experimental hash profile, not a finalized Maheshwara Hash construction.")

with tabs[6]:
    st.subheader("Batch processing")
    st.write("Upload a UTF-8 CSV containing a column named `text`. Batch output is encrypted row-by-row with independent salts/nonces.")
    csv_file = st.file_uploader("CSV file", type=["csv"])
    batch_pw = st.text_input("Batch passphrase", type="password", key="batch_pw")
    if csv_file and batch_pw:
        import csv, io
        try:
            rows = list(csv.DictReader(io.StringIO(csv_file.getvalue().decode("utf-8-sig"))))
            if not rows or "text" not in rows[0]:
                st.error("CSV must contain a 'text' column.")
            elif st.button("Encrypt CSV rows"):
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["row", "encrypted_payload"])
                writer.writeheader()
                for idx, row in enumerate(rows, 1):
                    writer.writerow({"row": idx, "encrypted_payload": encrypt_payload(row["text"], batch_pw, False, "Literal characters")})
                data = out.getvalue()
                st.success(f"Encrypted {len(rows)} rows.")
                st.download_button("Download encrypted CSV", data, "plc_batch_encrypted.csv", "text/csv")
        except Exception as e:
            st.error(f"Batch processing error: {e}")

with tabs[7]:
    st.subheader("Mapping and research notes")
    st.markdown("""
    **Research lineage preserved in this starter release**
    - 3D prototype: place / manner / Bhāva-or-intensity concept.
    - English PLC proposal: place of articulation / manner / voicing / phoneme class.
    - Sanskrit proposal: Bhūta / Rasa / Kāla / Varṇa-cluster conceptual axes.
    - Expanded Streamlit prototype: articulation, manner, voicing, class, Bhāva, position; later proposals included Chakra and timing dimensions.
    - Experimental cryptographic direction: Ring-LWE-inspired vector perturbation and grammar shuffling were proposals, not production-ready or validated cryptography.
    - Maheshwara Sutra organization is a phonological foundation; this app's starter feature table is not a canonical encoding of the Sutras.

    **Important security boundary**
    - AES-256-GCM is the actual encryption layer.
    - Base64 and lattice coordinates are representations, not secrecy mechanisms.
    - The lattice profile is deterministic and intended for experimentation, not cryptographic key generation.
    - No cloud database, telemetry, account system, or server-side password storage is included.
    """)
    st.download_button("Download starter mapping CSV", mapping_csv_template(), "plc_mapping_template.csv", "text/csv")
    st.markdown("**Free-tier deployment**")
    st.code("1. Upload this project to a GitHub repository\n2. In Streamlit Community Cloud, choose the repository and app.py\n3. Deploy. No paid API keys are required.")


with tabs[8]:
    st.subheader("Sanskrit Sandhi Lab — limited starter rules")
    st.warning("This is a small, explicit vowel-sandhi demonstrator, not a complete Aṣṭādhyāyī engine. It does not infer morphology, accents, or all contextual conditions.")
    left = st.selectbox("Left vowel", ["a","ā","i","u"], key="sandhi_left")
    right = st.selectbox("Right vowel", ["a","ā","i","u","e","o"], key="sandhi_right")
    if st.button("Apply listed sandhi rule"):
        results = sandhi.apply(left, right)
        if results:
            for item in results: st.write(f"**{item['rule']} → {item['result']}** — {item['explanation']}")
        else: st.info("No rule for this exact pair is implemented in this starter table.")
    surface = st.text_input("Explore possible reverse analyses", "devaindra", key="sandhi_surface")
    if st.button("Find candidate splits"):
        candidates = sandhi.analyze(surface)
        if candidates: st.json(candidates)
        else: st.info("No candidate found in the limited rule table. Absence is not proof that no Sanskrit analysis exists.")

with tabs[9]:
    st.subheader("Bhāva-weighted phoneme vectors")
    st.caption("Numeric weights and phoneme associations are user-defined. No universal or scriptural numeric scale is assumed.")
    with st.form("bhava_vector_form"):
        phoneme = st.text_input("Phoneme / token (optional)")
        bhava = st.selectbox("Bhāva", bhava_vectors.BHAVAS)
        chakra = st.selectbox("Chakra (optional)", [""] + bhava_vectors.CHAKRAS)
        rasa = st.selectbox("Rasa (optional)", [""] + bhava_vectors.RASAS)
        weight = st.slider("User-assigned weight", -1.0, 1.0, 1.0, 0.05)
        submitted = st.form_submit_button("Add vector")
    if "bhava_vectors" not in st.session_state: st.session_state["bhava_vectors"] = []
    if submitted:
        try:
            st.session_state["bhava_vectors"].append(bhava_vectors.vector(bhava, chakra, rasa, weight, phoneme))
            st.success("Vector added to this session.")
        except Exception as exc: st.error(str(exc))
    if st.session_state["bhava_vectors"]:
        st.dataframe(st.session_state["bhava_vectors"], use_container_width=True)
        st.download_button("Export vectors JSON", bhava_vectors.export_json(st.session_state["bhava_vectors"]),
                           "plc_bhava_vectors.json", "application/json")
        st.download_button("Export vectors CSV",
                           "phoneme,bhava,chakra,rasa,weight\n" + "\n".join(
                               ",".join(str(row[k]).replace(",", " ") for k in ["phoneme","bhava","chakra","rasa","weight"])
                               for row in st.session_state["bhava_vectors"]),
                           "plc_bhava_vectors.csv", "text/csv")
    st.caption("Your previously supplied examples — “ma” → Rāgaḥ / Anāhata / Śṛṅgāra and “ha” → Krodhaḥ / Maṇipūra / Raudra — can be entered as research hypotheses, not treated as validated universal mappings.")

with tabs[10]:
    st.subheader("Trishula lattice perturbation — visualization experiment")
    st.warning("Not encryption, not a key-agreement scheme, and not cryptographically secure. The transform is a reversible coordinate experiment whose offsets are visible.")
    source = st.text_area("Text to encode", "namaḥ śivāya", key="trishula_text")
    c1,c2,c3 = st.columns(3)
    with c1: dx = st.number_input("Arm 1 offset", value=1, step=1)
    with c2: dy = st.number_input("Arm 2 offset", value=2, step=1)
    with c3: dz = st.number_input("Arm 3 offset", value=3, step=1)
    mod = st.number_input("Modulus", min_value=2, max_value=256, value=17, step=1)
    if st.button("Run Trishula perturbation"):
        encoded = plc_core.encode(source)
        changed = trishula_lab.transform(encoded["records"], (int(dx),int(dy),int(dz)), int(mod))
        restored = trishula_lab.reverse(changed, (int(dx),int(dy),int(dz)), int(mod))
        st.json({"offsets":[int(dx),int(dy),int(dz)],"modulus":int(mod),"sample":changed[:8],
                 "round_trip_verified":restored == encoded["records"]})
        st.caption("The first three coordinate fields are transformed modulo the selected modulus. Original coordinates are retained as experiment metadata for reversal; this is intentionally not a secure encoding.")

with tabs[11]:
    st.subheader("Hash performance benchmark")
    st.caption("Local microbenchmark only. Results vary by device, Python build, and load; speed does not indicate cryptographic strength.")
    bench_text = st.text_area("Benchmark payload", "PLC Studio benchmark sample " * 100, key="bench_text")
    repeats = st.slider("Iterations", 10, 2000, 250, 10)
    if st.button("Run local benchmark"):
        data = bench_text.encode("utf-8")
        funcs = {
            "SHA-256": lambda: hashlib.sha256(data).digest(),
            "SHA3-512": lambda: hashlib.sha3_512(data).digest(),
            "BLAKE2b-512": lambda: hashlib.blake2b(data, digest_size=64).digest(),
        }
        rows=[]
        for name, fn in funcs.items():
            start=time.perf_counter()
            for _ in range(repeats): fn()
            elapsed=time.perf_counter()-start
            rows.append({"algorithm":name,"iterations":repeats,"total_ms":round(elapsed*1000,3),
                         "microseconds_per_call":round(elapsed*1e6/repeats,3)})
        st.dataframe(rows, use_container_width=True)
        st.caption(f"Payload size: {len(data)} bytes. This is not a security evaluation or a controlled benchmark.")


with tabs[12]:
    st.subheader("PLC 3.0 — Pāṇinian phonological rule engine")
    st.markdown("An inspectable rule registry connects selected external vowel-sandhi rules to the PLC phoneme workflow.")
    st.warning("This is a bounded research implementation, not a complete Aṣṭādhyāyī interpreter. Rule conditions, adhikāras, anuvṛtti, exceptions, morphology, accent, and all rule conflicts are not yet modeled.")
    left_word = st.text_input("Left word / stem (IAST)", "deva", key="engine_left")
    right_word = st.text_input("Right word / stem (IAST)", "indra", key="engine_right")
    if st.button("Apply boundary rules"):
        try:
            matches = panini_engine.apply_boundary(left_word.strip(), right_word.strip())
            if matches:
                st.session_state["panini_engine_matches"] = matches
                for m in matches:
                    st.markdown(f"**{m['result']}** — {m['name']} ({m['sutra']})")
                    st.caption(f"{m['rule_id']} · Boundary: {m['boundary']} · {m['explanation']}")
            else:
                st.info("No implemented rule matched the final/initial vowel boundary.")
        except Exception as exc:
            st.error(str(exc))
    st.divider()
    st.markdown("**Candidate reverse reconstruction**")
    surface_word = st.text_input("Surface form (IAST)", "devendra", key="engine_surface")
    if st.button("Generate possible underlying splits"):
        candidates = panini_engine.reverse_candidates(surface_word.strip())
        if candidates:
            st.dataframe(candidates, use_container_width=True)
            st.caption("These are mechanically generated candidates. They are not ranked grammatical analyses or unique reconstructions.")
        else:
            st.info("No candidate generated by the current rule registry.")
    st.divider()
    st.markdown("**Implemented rule registry**")
    st.dataframe(panini_engine.rule_catalog(), use_container_width=True)
    st.download_button("Download rule registry JSON",
        json.dumps({"format":"PLC-PANINI-RULES-1","rules":panini_engine.rule_catalog()}, ensure_ascii=False, indent=2),
        "plc_panini_rule_registry.json", "application/json")
    st.divider()
    st.markdown("**Documented coordinate profile**")
    st.json(panini_engine.explain_coordinate_profile())
    st.download_button("Download coordinate specification",
        json.dumps(panini_engine.explain_coordinate_profile(), ensure_ascii=False, indent=2),
        "plc_coordinate_specification.json", "application/json")
