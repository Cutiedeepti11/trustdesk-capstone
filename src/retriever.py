import os
import re

KB_DOCS = {}


def load_kb(kb_path="data/knowledge_base"):
    global KB_DOCS
    KB_DOCS = {}
    if not os.path.exists(kb_path):
        return

    for fname in os.listdir(kb_path):
        if fname.endswith(".md"):
            with open(os.path.join(kb_path, fname), "r", encoding="utf-8") as f:
                content = f.read()
                # Extract Doc ID from frontmatter/heading or filename
                match = re.search(r"KB-[A-Z]+-[0-9]+", content)
                doc_id = match.group(0) if match else fname.replace(".md", "").upper()
                KB_DOCS[doc_id] = content


def search_kb(query: str, top_k: int = 3):
    query_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for doc_id, text in KB_DOCS.items():
        text_words = set(re.findall(r"\w+", text.lower()))
        overlap = len(query_words.intersection(text_words))
        scored.append((overlap, doc_id, text))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored[:top_k]

    context = ""
    retrieved_ids = []
    for score, doc_id, text in top_matches:
        retrieved_ids.append(doc_id)
        context += f"--- Document [{doc_id}] ---\n{text}\n\n"
    return context, retrieved_ids