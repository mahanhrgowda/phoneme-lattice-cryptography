# PLC Studio 3.0 — Phoneme Lattice Cryptography

A free-tier Streamlit workbench inspired by the user's prior PLC, Maheshwara Lattice,
Maheshwara Hash, Sanskrit phonology, and English phoneme-mapping research.

## Features
- Password-based authenticated encryption: AES-256-GCM
- Scrypt password-based key derivation with random salt
- Base64 JSON envelope for portable encrypted payloads
- Decryption with authentication/integrity verification
- Reversible starter lattice representation
- IAST/Sanskrit-oriented longest-match tokenization
- Literal-character mode for lossless experiments with arbitrary text
- SHA-256 and HMAC-SHA256
- CSV batch encryption
- JSON lattice import/export
- 14 Maheshwara Sūtra reference panel
- Preserved 22-Bhāva catalogue
- User-defined 4D axes (Bhūta, Rasa, Kāla, Varṇa cluster)
- Educational toy LWE keygen/encrypt/decrypt demonstration (explicitly insecure)
- Encrypted-payload QR generation and PNG download

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy free on Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. Create a Community Cloud app.
3. Select the repository and `app.py`.
4. Deploy. No paid API key is required.

## Important: research fidelity and limitations
The prior research notes describe several conceptual and prototype architectures:
- 3D: place / manner / Bhāva-or-intensity
- English 4D: place of articulation / manner / voicing / phoneme class
- Sanskrit 4D: Bhūta / Rasa / Kāla / Varṇa cluster
- 6D/7D proposals adding Bhāva, Chakra, and timing/position
- Ring-LWE-inspired perturbation and grammar shuffling as experimental proposals

The available historical notes do **not** contain a complete finalized numeric coordinate dictionary,
key schedule, modulus/matrix specification, or canonical reverse-tokenization rules. Therefore this
release explicitly labels its feature map as a **starter profile**, not as a recovered historical
mapping. Extend the mapping only when the intended coordinates and rules are documented.

## Security
AES-256-GCM is the actual confidentiality and integrity mechanism. Scrypt derives a key from
the passphrase. A fresh random salt and nonce are generated for each encryption. The passphrase
is not stored by the app.

Do not treat Base64, hashes, phoneme coordinates, QR codes, or lattice transformations as
encryption. Do not use this experimental app to protect high-value secrets without an independent
security review. Keep backups of important plaintext and encrypted payloads.

## File format
Encrypted payloads are Base64-encoded JSON envelopes with:
- `format`: `PLC-AESGCM-1`
- KDF metadata and random salt
- AES-GCM nonce
- ciphertext + authentication tag

Lattice JSON uses `PLC-LATTICE-1`. Literal-character mode is lossless for the original
character stream. IAST/Sanskrit mode tokenizes known phoneme sequences and preserves unknown
characters as literal tokens.

## Project layout
- `app.py` — Streamlit application
- `requirements.txt` — minimal dependencies for Community Cloud
- `data/` — reserved for future user-supplied mapping files


## PLC Studio 2.0 additions
- Sūtra reference list (14 Śiva Sūtras); not yet a complete pratyāhāra grammar/parser.
- User's 22 Bhāva labels preserved as a catalogue; no unsupported numeric weights are assumed.
- User-defined 4D lattice axes preserved exactly: X=Bhūta, Y=Rasa, Z=Kāla, W=Varṇa cluster.
- An educational tiny-parameter LWE demonstration is included to explore noisy linear equations and public-key encryption. It is deliberately insecure and must never protect real data.
- The LWE demo is not Ring-LWE, FrodoKEM, or ML-KEM. The production-facing confidentiality feature remains AES-256-GCM with Scrypt-derived keys.

## Version 2.1 — Bidirectional codebook
- Added `plc_core.py`, a deterministic NFC-normalized IAST tokenizer and stable six-dimensional codebook.
- Coordinate axes: place, manner, voicing, phoneme class, Bhāva slot, stable token ID.
- The token ID is a unique reversible codebook index. It is not represented as an ancient or traditional Maheshwara coordinate.
- Decoding verifies every token-coordinate pair and rejects tampering. Repeated phonemes are permitted and decode in sequence.
- Run round-trip tests with `python -m unittest test_plc_core.py`.
- This codebook is a new explicit engineering profile. It does not claim to reconstruct the user's incomplete historical mapping.


## Version 2.2 — Devanagari and lattice projections
- Added lightweight Devanagari-to-IAST transliteration for common Sanskrit orthography.
- Added configurable 3D, 4D, 6D and 7D projections over the deterministic codebook.
- Kept the conceptual Bhūta–Rasa–Kāla–Varṇa axes separate from the articulatory feature coordinates.
- Transliteration is orthographic only; no sandhi, morphology, Vedic accents or grammar inference is claimed.


## Version 2.3 — Pratyāhāra and Bhāva mapping workbench
- Added a standard 14 Śiva-sūtra sequence and a range-based pratyāhāra explorer.
- Handles repeated start varṇas and it-markers by explicit occurrence selection.
- Added a user-editable Bhāva–Chakra–Rasa association workbench with CSV/JSON export and CSV import.
- The app does not preassign speculative Bhāva/Chakra/Rasa correspondences.
- This is not a complete Pāṇinian grammar engine or Aṣṭādhyāyī interpreter.


## Version 2.4 — Sandhi, vectors, Trishula experiment, SHA3-512
- Added a limited, inspectable vowel-sandhi rule table and candidate reverse-analysis helper. This is not a complete Sanskrit sandhi or Pāṇinian grammar engine.
- Added user-defined Bhāva–Chakra–Rasa–phoneme vectors with editable weights and JSON/CSV export. No numeric correspondences are pre-populated as facts.
- Added reversible three-arm Trishula coordinate perturbation for visualization experiments only. It is not encryption or a cryptographic primitive.
- Added SHA3-512 and HMAC-SHA3-512 digest options.
- Added a local SHA-256 / SHA3-512 / BLAKE2b-512 microbenchmark. Timings are device-dependent and are not security comparisons.
- Automated tests cover sandhi examples, vector validation, Trishula round-trip, and existing lattice/transliteration/pratyāhāra behavior.

## Research and security boundaries
The new sandhi inventory is intentionally incomplete. Reverse analyses are candidates, not unique derivations. Bhāva vectors are user-authored hypotheses. Trishula offsets and the starter lattice coordinates are transparent reversible data transformations, not cryptographic security. Use AES-256-GCM with Scrypt for confidentiality in this app; for production systems, use independently reviewed, standardized cryptographic libraries and protocols.


## Version 3.0 — Pāṇinian phonological engine research release
- Added `panini_engine.py`, an inspectable registry of selected external vowel-sandhi rules, including rule IDs, sūtra references, boundary classes, replacements, explanations, and a simple application pipeline.
- Implemented a boundary composer for selected savarṇa-dīrgha, guṇa, vṛddhi, yaṇ, and eco'yavāyāvaḥ examples.
- Added candidate reverse reconstruction. It enumerates possible splits from the listed transformations; it is not a unique or ranked grammatical parser.
- Added `coordinate_spec.json` and an in-app specification download describing the six-dimensional PLC-CODEBOOK-2 coordinate profile and separately preserving the conceptual X=Bhūta, Y=Rasa, Z=Kāla, W=Varṇa-cluster axes.
- Added regression tests for guṇa and yaṇ boundary transformations and the coordinate specification.

### PLC-CODEBOOK-2 coordinate contract
| Index | Field | Meaning |
|---:|---|---|
| 0 | place | Broad place-of-articulation category |
| 1 | manner | Broad manner-of-articulation category |
| 2 | voicing | Starter binary voicing feature |
| 3 | phoneme_class | Vowel/consonant/other class |
| 4 | bhava_slot | Reserved user-defined Bhāva slot; currently zero |
| 5 | token_id | Stable reversible codebook index |

The coordinate contract is a documented software convention. The semantic 4D axes (Bhūta, Rasa, Kāla, Varṇa cluster) remain a separate conceptual model and are not silently substituted for these six codebook fields.

### Engine limitations
The Pāṇinian engine implements a deliberately selected subset of external vowel sandhi. It is not a complete Aṣṭādhyāyī interpreter: it does not yet implement the full rule inventory, adhikāra and anuvṛtti propagation, all paribhāṣās, exception resolution, morphological analysis, accent, or complete Sanskrit orthographic/phonological handling. Sūtra references identify the rule families represented in this starter registry; the implementation is not a scholarly critical edition of every rule's full conditions.
