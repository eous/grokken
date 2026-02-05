#!/usr/bin/env python3
"""
Command-line interface for grokken.

Usage:
    grokken process --barcode 32044010149714 --source data/raw/principia.parquet
    grokken process --collection principia --source data/raw/principia.parquet
    grokken list
    grokken list --collection principia
    grokken info --barcode 32044010149714
    grokken generate --config config.yaml
    grokken analyze --source data.parquet
    grokken segment --source data.parquet --barcode 32044010149714
"""

import argparse
import sys
from pathlib import Path

from grokken.registry import registry


def cmd_list(args: argparse.Namespace) -> int:
    """List available book processors."""
    if args.collection:
        processors = registry.get_collection(args.collection)
        if not processors:
            print(f"No processors found in collection: {args.collection}")
            return 1

        print(f"Collection: {args.collection} ({len(processors)} books)")
        print("-" * 60)
        for proc_cls in processors:
            print(f"  {proc_cls.barcode}: {proc_cls.title[:50]}")
    else:
        collections = registry.list_collections()
        if not collections:
            print("No book processors registered.")
            print("Add processors to grokken/books/ to get started.")
            return 0

        print(f"Registered collections: {len(collections)}")
        print("-" * 60)
        for coll in sorted(collections):
            procs = registry.get_collection(coll)
            print(f"  {coll}: {len(procs)} books")

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show info about a specific book processor."""
    proc_cls = registry.get(args.barcode)
    if not proc_cls:
        print(f"No processor found for barcode: {args.barcode}")
        return 1

    print(f"Barcode: {proc_cls.barcode}")
    print(f"Title: {proc_cls.title}")
    print(f"Author: {proc_cls.author}")
    print(f"Date: {proc_cls.date}")
    print(f"Transforms: {len(proc_cls.transforms)}")
    for i, t in enumerate(proc_cls.transforms, 1):
        name = getattr(t, "__name__", str(t))
        print(f"  {i}. {name}")
    if proc_cls.notes:
        print(f"\nNotes:\n{proc_cls.notes}")

    return 0


def cmd_process(args: argparse.Namespace) -> int:
    """Process book(s) through their pipelines."""
    source = Path(args.source)
    if not source.exists():
        print(f"Source file not found: {source}")
        return 1

    import pandas as pd

    df = pd.read_parquet(source)

    if args.barcode:
        # Process single book
        proc_cls = registry.get(args.barcode)
        if not proc_cls:
            print(f"No processor found for barcode: {args.barcode}")
            return 1

        processors = [proc_cls]
    elif args.collection:
        # Process collection
        processors = registry.get_collection(args.collection)
        if not processors:
            print(f"No processors found in collection: {args.collection}")
            return 1
    else:
        print("Must specify --barcode or --collection")
        return 1

    # Process each book
    results = []
    errors = 0
    for proc_cls in processors:
        print(f"Processing: {proc_cls.title[:50]}...")
        proc = proc_cls()
        try:
            proc.run(df)
            stats = proc.stats()
            results.append(
                {
                    "text": proc.processed_text,
                    **stats,
                }
            )
            print(
                f"  Done: {stats['raw_chars']:,} -> {stats['processed_chars']:,} chars "
                f"({stats['reduction_pct']}% reduction)"
            )
        except (KeyError, ValueError) as e:
            errors += 1
            print(f"  Error processing {proc_cls.barcode}: {e}", file=sys.stderr)
        except Exception as e:
            errors += 1
            print(
                f"  Error processing {proc_cls.barcode}: {type(e).__name__}: {e}", file=sys.stderr
            )

    # Save results
    if results and args.output:
        output = Path(args.output)
        result_df = pd.DataFrame(results)

        if output.suffix == ".parquet":
            result_df.to_parquet(output, index=False)
        elif output.suffix == ".jsonl":
            result_df.to_json(output, orient="records", lines=True)
        else:
            result_df.to_csv(output, index=False)

        print(f"\nSaved {len(results)} processed books to {output}")

    if errors and not results:
        return 1
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="grokken",
        description="Deep understanding and transformation of historical texts.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List available processors")
    list_parser.add_argument("--collection", "-c", help="List only this collection")

    # info command
    info_parser = subparsers.add_parser("info", help="Show info about a processor")
    info_parser.add_argument("--barcode", "-b", required=True, help="Book barcode")

    # process command
    proc_parser = subparsers.add_parser("process", help="Process book(s)")
    proc_parser.add_argument("--barcode", "-b", help="Process single book by barcode")
    proc_parser.add_argument("--collection", "-c", help="Process all books in collection")
    proc_parser.add_argument("--source", "-s", required=True, help="Source parquet file")
    proc_parser.add_argument("--output", "-o", help="Output file (parquet, jsonl, or csv)")

    # Add generation commands
    try:
        from grokken.generation.cli import add_generate_subparsers

        add_generate_subparsers(subparsers)
    except ImportError:
        # Generation dependencies not installed
        pass

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "process":
        return cmd_process(args)
    elif hasattr(args, "func"):
        # Generation commands use func pattern
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
