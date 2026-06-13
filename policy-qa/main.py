import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Local Policy Q&A — runs entirely offline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  ingest          Parse policies/, embed, and store in ChromaDB
  ingest --force  Re-ingest from scratch (clears existing index)
  query           Answer questions in questions.xlsx -> output/answers.xlsx
  query --questions path/to/file.xlsx  Use a different questions file
  run             Ingest then query (full pipeline in one shot)
        """,
    )
    sub = parser.add_subparsers(dest="command")

    ingest_p = sub.add_parser("ingest", help="Build the policy vector index")
    ingest_p.add_argument("--force", action="store_true", help="Re-ingest from scratch")

    query_p = sub.add_parser("query", help="Answer questions from an Excel file")
    query_p.add_argument("--questions", type=str, help="Path to questions .xlsx file")
    query_p.add_argument("--output", type=str, help="Path for answers .xlsx file")

    run_p = sub.add_parser("run", help="Ingest then query (full pipeline)")
    run_p.add_argument("--force", action="store_true", help="Re-ingest from scratch")
    run_p.add_argument("--questions", type=str, help="Path to questions .xlsx file")
    run_p.add_argument("--output", type=str, help="Path for answers .xlsx file")

    args = parser.parse_args()

    if args.command == "ingest":
        from src.ingest import build_index
        build_index(force=args.force)

    elif args.command == "query":
        from src.query import run
        from src.config import QUESTIONS_FILE, OUTPUT_FILE
        run(
            questions_file=Path(args.questions) if args.questions else QUESTIONS_FILE,
            output_file=Path(args.output) if args.output else OUTPUT_FILE,
        )

    elif args.command == "run":
        from src.ingest import build_index
        from src.query import run
        from src.config import QUESTIONS_FILE, OUTPUT_FILE
        build_index(force=args.force)
        run(
            questions_file=Path(args.questions) if args.questions else QUESTIONS_FILE,
            output_file=Path(args.output) if args.output else OUTPUT_FILE,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
