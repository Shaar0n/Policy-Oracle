# Policy Q&A - Local RAG System

A fully offline, privacy-first question-answering system for policy documents. Drop in your PDFs, Word docs, and text files, provide a spreadsheet of questions, and get answers with source citations written back to Excel — all running locally on your machine with no data sent to external APIs.

---

## How It Works

This system uses **Retrieval-Augmented Generation (RAG)**:

```
Policy files (PDF / DOCX / TXT)
        │
        ▼
  Parse & extract text
        │
        ▼
  Chunk + embed locally (nomic-embed-text)
        │
        ▼
  Store in ChromaDB (vector index on disk)
        │
        ◄─────────── Question from Excel
        │
        ▼
  Retrieve top-k relevant chunks
        │
        ▼
  Local LLM answers (qwen2.5:14b via Ollama)
        │
        ▼
  Answer + Source + Confidence written to Excel
```

Every component runs locally — embeddings, vector search, and the LLM. Nothing leaves your machine.

---

## Features

- **100% offline** — works air-gapped after initial model download
- **Multi-format ingestion** — PDF (text-based), DOCX, DOC, TXT, Markdown
- **Source citations** — every answer cites the exact file and page number
- **Confidence scoring** — High / Medium / Low based on retrieval similarity
- **Hallucination guard** — model is instructed to say "Not found in the provided policies" rather than guess
- **Excel in, Excel out** — reads your question spreadsheet, writes answers beside each question
- **Persistent index** — re-ingest only when policies change, not every run

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (local LLM runtime)
- NVIDIA GPU recommended (tested on RTX 4080 Laptop, 12 GB VRAM)
- CPU-only works but is significantly slower

---

## Setup

### 1. Install Ollama

Download and install from [ollama.com/download](https://ollama.com/download).

### 2. Pull the models

```bash
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

`qwen2.5:14b` is ~9 GB. After this, everything runs offline.

### 3. Clone the repo and install dependencies

```bash
git clone https://github.com/your-username/policy-qa.git
cd policy-qa
python -m venv .venv

# Windows
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Usage

### Step 1 — Add your files

```
policy-qa/
├── policies/        ← drop all policy documents here (subfolders supported)
└── questions.xlsx   ← one question per row; column header must contain "question"
```

If your Excel has no header row, the system detects this automatically and reads all rows as questions.

### Step 2 — Ingest policies

```bash
python main.py ingest
```

This parses all documents, chunks them, generates embeddings, and stores them in a local ChromaDB index. Run once — or re-run with `--force` when policies change.

```bash
python main.py ingest --force   # rebuild index from scratch
```

### Step 3 — Answer questions

```bash
python main.py query
```

Reads `questions.xlsx`, retrieves relevant policy chunks for each question, generates answers, and writes results to `output/answers.xlsx`.

### Full pipeline in one command

```bash
python main.py run
```

### Custom file paths

```bash
python main.py query --questions path/to/myquestions.xlsx --output path/to/results.xlsx
```

---

## Output

The output Excel adds three columns beside your original questions:

| Question | Answer | Sources | Confidence |
|---|---|---|---|
| What is the data retention period? | Records are retained for 7 years after account closure. | `data-policy.pdf p.4` | High |
| Who approves policy exceptions? | The Information Security Officer must approve all exceptions. | `access-policy.docx p.2` | High |
| Does this cover dental claims? | Not found in the provided policies. | — | — |

- **Answer** — grounded response from the LLM, based only on retrieved policy text
- **Sources** — file name and page number for manual verification
- **Confidence** — based on cosine similarity between the question and retrieved chunks

---

## Project Structure

```
policy-qa/
├── policies/              # source documents (input)
├── data/chroma/           # persisted vector index (auto-created)
├── output/                # results written here
├── src/
│   ├── config.py          # all settings in one place
│   ├── parsers.py         # PDF / DOCX / TXT text extractors
│   ├── ingest.py          # parse → chunk → embed → store
│   ├── llm.py             # prompt builder + Ollama chat client
│   └── query.py           # read Excel → retrieve → answer → write Excel
├── main.py                # CLI entry point
└── requirements.txt
```

---

## Configuration

All settings are in `src/config.py`:

| Setting | Default | Description |
|---|---|---|
| `LLM_MODEL` | `qwen2.5:14b` | Ollama model used for answering |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama model used for embeddings |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service URL |
| `CHUNK_SIZE` | `3200` chars | Size of each text chunk (~800 tokens) |
| `CHUNK_OVERLAP` | `400` chars | Overlap between consecutive chunks |
| `TOP_K` | `5` | Number of chunks retrieved per question |
| `EMBED_BATCH_SIZE` | `32` | Chunks embedded per Ollama call |
| `QUESTION_COLUMN` | `"question"` | Substring to detect the question column (case-insensitive) |

---

## Supported File Types

| Format | Extension |
|---|---|
| PDF (text-based) | `.pdf` |
| Microsoft Word | `.docx`, `.doc` |
| Plain text | `.txt` |
| Markdown | `.md` |

> Scanned PDFs (image-based) are not currently supported. OCR support can be added via `pytesseract`.

---

## Tech Stack

| Component | Library |
|---|---|
| LLM runtime | [Ollama](https://ollama.com) |
| LLM model | [Qwen2.5:14b](https://ollama.com/library/qwen2.5) |
| Embeddings | [nomic-embed-text](https://ollama.com/library/nomic-embed-text) |
| Vector store | [ChromaDB](https://www.trychroma.com) |
| PDF parsing | [PyMuPDF](https://pymupdf.readthedocs.io) |
| DOCX parsing | [python-docx](https://python-docx.readthedocs.io) |
| Excel I/O | [pandas](https://pandas.pydata.org) + [openpyxl](https://openpyxl.readthedocs.io) |

---

## License

MIT
