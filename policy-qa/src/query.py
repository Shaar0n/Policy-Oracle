import pandas as pd
import chromadb
import ollama
from pathlib import Path

from src.config import (
    CHROMA_DIR,
    OUTPUT_FILE,
    OUTPUT_DIR,
    QUESTIONS_FILE,
    TOP_K,
    EMBED_MODEL,
    OLLAMA_HOST,
    QUESTION_COLUMN,
)
from src.llm import ask


def _embed_query(text: str) -> list[float]:
    client = ollama.Client(host=OLLAMA_HOST)
    resp = client.embed(model=EMBED_MODEL, input=[text])
    return resp.embeddings[0]


def _retrieve(collection, question: str) -> list[dict]:
    emb = _embed_query(question)
    results = collection.query(
        query_embeddings=[emb],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {"text": doc, "file": meta["file"], "page": meta["page"], "distance": dist}
        )
    return chunks


def _confidence(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    avg = sum(c["distance"] for c in chunks) / len(chunks)
    # Cosine distance: 0 = identical, 1 = orthogonal — lower is better
    if avg < 0.2:
        return "High"
    if avg < 0.5:
        return "Medium"
    return "Low"


def _detect_question_col(df: pd.DataFrame) -> str:
    for col in df.columns:
        if QUESTION_COLUMN.lower() in str(col).lower():
            return col
    return df.columns[0]


def _format_sources(chunks: list[dict]) -> str:
    seen, parts = set(), []
    for c in chunks:
        key = f"{c['file']} p.{c['page']}"
        if key not in seen:
            seen.add(key)
            parts.append(key)
    return "; ".join(parts)


def run(questions_file: Path = QUESTIONS_FILE, output_file: Path = OUTPUT_FILE):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = chroma.get_collection("policies")
    except Exception:
        raise RuntimeError(
            "Policy index not found. Run ingestion first:\n"
            "  python main.py ingest"
        )

    df = pd.read_excel(questions_file)

    # If the first column looks like a question (no proper header), re-read without header
    first_col = str(df.columns[0])
    has_header = any(QUESTION_COLUMN.lower() in str(c).lower() for c in df.columns)
    if not has_header and (len(first_col) > 20 or "?" in first_col):
        df = pd.read_excel(questions_file, header=None)
        df.columns = ["Question"] + [f"col_{i}" for i in range(1, len(df.columns))]

    q_col = _detect_question_col(df)
    print(f"Question column: '{q_col}' | {len(df)} questions\n")

    answers, sources, confidences = [], [], []

    for i, row in df.iterrows():
        question = str(row[q_col]).strip()

        if not question or question.lower() == "nan":
            answers.append("")
            sources.append("")
            confidences.append("")
            continue

        print(f"[{i + 1}/{len(df)}] {question[:90]}")
        chunks = _retrieve(collection, question)

        if not chunks:
            answers.append("Not found in the provided policies.")
            sources.append("")
            confidences.append("")
            print("  -> No relevant chunks found.\n")
            continue

        answer = ask(question, chunks)
        src = _format_sources(chunks)
        conf = _confidence(chunks)

        answers.append(answer)
        sources.append(src)
        confidences.append(conf)
        print(f"  -> [{conf}] {src}\n")

    df["Answer"] = answers
    df["Sources"] = sources
    df["Confidence"] = confidences

    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default=str(QUESTIONS_FILE))
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    args = parser.parse_args()
    run(Path(args.questions), Path(args.output))
