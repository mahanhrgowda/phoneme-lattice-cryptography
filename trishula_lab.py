"""Reversible Trishula coordinate perturbation for visualization only."""
def transform(records, offsets=(1, 2, 3), modulus=17):
    if len(offsets) != 3 or modulus < 2: raise ValueError("Three offsets and modulus >= 2 required.")
    out=[]
    for rec in records:
        coord=list(rec["coordinate"])
        if len(coord) < 3: raise ValueError("Each coordinate needs at least three axes.")
        original=coord[:]
        for axis,delta in enumerate(offsets): coord[axis]=(coord[axis]+int(delta)) % modulus
        out.append({"token":rec["token"],"coordinate":coord,"original":original})
    return out
def reverse(records, offsets=(1, 2, 3), modulus=17):
    out=[]
    for rec in records:
        coord=list(rec["coordinate"])
        for axis,delta in enumerate(offsets): coord[axis]=(coord[axis]-int(delta)) % modulus
        if coord != rec["original"]: raise ValueError("Perturbation metadata mismatch.")
        out.append({"token":rec["token"],"coordinate":coord})
    return out
