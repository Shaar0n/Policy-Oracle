from pathlib import Path

ROOT = Path(__file__).parent.parent

POLICIES_DIR = ROOT / "policies"
CHROMA_DIR = ROOT / "data" / "chroma"
OUTPUT_DIR = ROOT / "output"
QUESTIONS_FILE = ROOT / "questions.xlsx"
OUTPUT_FILE = OUTPUT_DIR / "answers.xlsx"

# Ollama
LLM_MODEL = "qwen2.5:14b"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_HOST = "http://localhost:11434"

# Chunking (characters; ~4 chars per token)
CHUNK_SIZE = 3200   # ~800 tokens
CHUNK_OVERLAP = 400  # ~100 tokens

# Retrieval
TOP_K = 5
EMBED_BATCH_SIZE = 32

# Excel — column header containing the questions (case-insensitive substring match)
QUESTION_COLUMN = "question"
