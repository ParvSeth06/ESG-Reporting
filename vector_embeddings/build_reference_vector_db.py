import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

REFERENCE_FOLDER = "reference"
OUTPUT_FILE = "disclosure_vectors.json"

def load_reference_disclosures(folder):
    items = []

    for root, _, files in os.walk(folder):
        for fname in files:
            if fname.endswith(".txt"):
                path = os.path.join(root, fname)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                disclosure = fname.replace(".txt", "")
                topic = os.path.basename(root)

                items.append({
                    "topic": topic,
                    "disclosure": disclosure,
                    "content": content
                })

    return items


def build_vector_db():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    data = load_reference_disclosures(REFERENCE_FOLDER)
    vectors = []

    for item in data:
        emb = model.encode(item["content"])
        emb = np.array(emb, dtype=np.float32)

        vectors.append({
            "topic": item["topic"],
            "disclosure": item["disclosure"],
            "vector": emb.tolist(),
            "content": item["content"]
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(vectors, f, indent=2)

    print("✔ Disclosure-level vector DB created.")


if __name__ == "__main__":
    build_vector_db()
