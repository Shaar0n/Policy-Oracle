import ollama
from src.config import LLM_MODEL, OLLAMA_HOST

_SYSTEM = """You are a policy compliance assistant.
You will be given excerpts from company policy documents and a question.
Answer using ONLY the provided excerpts.
If the answer is not present in the excerpts, respond with exactly:
  Not found in the provided policies.
Be concise and precise. Do not speculate or add information not in the excerpts."""


def ask(question: str, chunks: list[dict]) -> str:
    """
    chunks: list of {text, file, page}
    Returns the model's answer as a string.
    """
    context = "\n\n---\n\n".join(
        f"[Source: {c['file']}, page {c['page']}]\n{c['text']}"
        for c in chunks
    )

    user_msg = (
        f"Policy excerpts:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer based only on the excerpts above."
    )

    client = ollama.Client(host=OLLAMA_HOST)
    resp = client.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    return resp.message.content.strip()
