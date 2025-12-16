import json
from sentence_transformers import SentenceTransformer

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build_company_embedding(input_txt, output_json="company_vector.json"):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    text = load_text(input_txt)
    embedding = model.encode(text).tolist()

    with open(output_json, "w") as f:
        json.dump({"embedding": embedding, "content": text}, f)

    print("Company embedding saved to", output_json)

if __name__ == "__main__":
    build_company_embedding(r"D:\ESG-reporting\ESG-Reporting\ingestor\output\ilovepdf_merged_clean.txt")
