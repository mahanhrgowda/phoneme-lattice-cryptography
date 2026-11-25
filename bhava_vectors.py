"""User-defined Bhāva vectors. No default numeric semantics are imposed."""
import json
BHAVAS = ["Śāntiḥ","Ānandaḥ","Bhaktiḥ","Jñānam","Karunā","Āstikyam","Vīryam","Utsāhaḥ","Rāgaḥ","Dainyaḥ","Harṣaḥ","Īrṣyā","Krodhaḥ","Bhayam","Vairāgyam","Mādhuryam","Dhṛtiḥ","Nirvedaḥ","Ākrośaḥ","Āścaryaṁ","Mohaḥ","Lajjā"]
CHAKRAS = ["Mūlādhāra","Svādhiṣṭhāna","Maṇipūra","Anāhata","Viśuddha","Ājñā","Sahasrāra"]
RASAS = ["Śṛṅgāra","Hāsya","Karuṇa","Raudra","Vīra","Bhayānaka","Bībhatsa","Adbhuta","Śānta"]
def vector(bhava, chakra="", rasa="", weight=1.0, phoneme=""):
    if bhava not in BHAVAS: raise ValueError("Unknown Bhāva label.")
    if chakra and chakra not in CHAKRAS: raise ValueError("Unknown Chakra label.")
    if rasa and rasa not in RASAS: raise ValueError("Unknown Rasa label.")
    if not -1.0 <= float(weight) <= 1.0: raise ValueError("Weight must be between -1 and 1.")
    return {"phoneme":phoneme, "bhava":bhava, "chakra":chakra, "rasa":rasa, "weight":float(weight)}
def export_json(rows):
    return json.dumps({"format":"PLC-BHAVA-VECTOR-1","records":rows}, ensure_ascii=False, indent=2)
