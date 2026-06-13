import chromadb
import ollama
from pathlib import Path

from src.config import (
    POLICIES_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBED_MODEL,
    EMBED_BATCH_SIZE,
    OLLAMA_HOST,
)
from src.parsers import parse_file, SUPPORTED_EXTENSIONS


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c]


def embed_batch(texts: list[str]) -> list[list[float]]:
    client = ollama.Client(host=OLLAMA_HOST)
    all_embeddings = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        resp = client.embed(model=EMBED_MODEL, input=batch)
        all_embeddings.extend(resp.embeddings)
    return all_embeddings


def build_index(force: bool = False) -> int:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if force:
        try:
            chroma.delete_collection("policies")
            print("Deleted existing index.")
        except Exception:
            pass

    collection = chroma.get_or_create_collection(
        "policies",
        metadata={"hnsw:space": "cosine"},
    )
    existing = collection.count()
    if existing > 0 and not force:
        print(f"Index already has {existing} chunks. Run with --force to re-ingest.")
        return existing

    files = [
        f for f in POLICIES_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    print(f"Found {len(files)} supported files in {POLICIES_DIR}")

    all_texts, all_ids, all_metas = [], [], []
    doc_id = 0

    for file in files:
        print(f"  Parsing: {file.name}")
        pages = parse_file(file)
        if not pages:
            print(f"    Skipped (empty or parse error)")
            continue

        for page in pages:
            for chunk in chunk_text(page["text"]):
                all_texts.append(chunk)
                all_ids.append(str(doc_id))
                all_metas.append({"file": page["file"], "page": page["page"]})
                doc_id += 1

        print(f"    -> {doc_id} chunks accumulated")

    if not all_texts:
        print("No text extracted. Check that policies/ contains supported files.")
        return 0

    print(f"\nEmbedding {len(all_texts)} chunks via {EMBED_MODEL}...")
    embeddings = embed_batch(all_texts)

    # Store in batches to avoid memory spikes
    batch = 500
    for i in range(0, len(all_texts), batch):
        collection.add(
            ids=all_ids[i : i + batch],
            embeddings=embeddings[i : i + batch],
            documents=all_texts[i : i + batch],
            metadatas=all_metas[i : i + batch],
        )
        print(f"  Stored {min(i + batch, len(all_texts))}/{len(all_texts)} chunks")

    print(f"\nIngestion complete. {doc_id} chunks indexed.")
    return doc_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-ingest even if index exists")
    args = parser.parse_args()
    build_index(force=args.force)
