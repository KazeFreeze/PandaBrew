import argparse
import sys
from pathlib import Path
import threading

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app import core

def main():
    parser = argparse.ArgumentParser(
        description="PandaBrew: A tool for selectively extracting project source code.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("source", type=str, help="The source directory to process.")
    parser.add_argument("output", type=str, help="The path to the output text file.")
    parser.add_argument("--include-file", type=str, help="Path to a file with include patterns.")
    parser.add_argument("--exclude-file", type=str, help="Path to a file with exclude patterns.")
    parser.add_argument("--filenames-only", action="store_true", help="Extract filenames only.")
    parser.add_argument("--show-excluded", action="store_true", help="Show excluded files in the structure view.")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.is_dir():
        print(f"Error: Source path '{args.source}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    def read_patterns_from_file(filepath: str) -> list[str]:
        if not filepath: return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        except FileNotFoundError:
            print(f"Warning: Pattern file not found: {filepath}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error reading pattern file {filepath}: {e}", file=sys.stderr)
            return []

    include_patterns = read_patterns_from_file(args.include_file)
    exclude_patterns = read_patterns_from_file(args.exclude_file)

    manual_selections = set()
    include_mode = True
    cancel_event = threading.Event()

    print(f"Starting extraction from '{source_path}'...")

    try:
        def progress_callback(progress, status):
            sys.stdout.write(f"\r  [{int(progress):>3}%] {status.ljust(60)}")
            sys.stdout.flush()

        processed_count = core.generate_report_to_file(
            output_file=args.output,
            source_path_str=str(source_path),
            include_mode=include_mode,
            manual_selections_str=manual_selections,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            filenames_only=args.filenames_only,
            show_excluded=args.show_excluded,
            cancel_event=cancel_event,
            progress_callback=progress_callback
        )

        print()
        print(f"Extraction complete. {processed_count} files processed and saved to '{args.output}'.")

    except Exception as e:
        print(f"\nAn error occurred during extraction: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
