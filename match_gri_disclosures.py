import json
import numpy as np
from numpy.linalg import norm

REFERENCE_DB = "reference_vectors.json"
COMPANY_VECTOR = "company_vector.json"

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (norm(a) * norm(b))

def match_disclosures():
    with open(REFERENCE_DB, "r") as f:
        standards = json.load(f)

    with open(COMPANY_VECTOR, "r") as f:
        company = json.load(f)

    company_vector = company["embedding"]

    ranked = []
    for std in standards:
        score = cosine_similarity(company_vector, std["embedding"])
        ranked.append((std["name"], score))

    ranked.sort(key=lambda x: x[1], reverse=True)

    print("\nTop Matches:")
    for name, score in ranked[:10]:
        print(f"{name}: {score:.4f}")

    return ranked

if __name__ == "__main__":
    match_disclosures()
