"""
CLI commands for the generation pipeline.

Provides `grokken generate` command for running the training data
generation pipeline.
"""

import argparse
import logging
from pathlib import Path
from typing import Any

from tqdm import tqdm

from grokken.generation.analyzer import BookAnalyzer
from grokken.generation.config import StrategyConfig, load_config
from grokken.generation.generator import Generator
from grokken.generation.segmenter import Segmenter

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_generate(args: argparse.Namespace) -> int:
    """Run the generation pipeline."""
    setup_logging(args.verbose)

    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1

    # Override config with CLI args if provided
    if args.output:
        config.output_dir = Path(args.output)

    # Create progress bar
    pbar = None

    def progress_callback(message: str, current: int, total: int) -> None:
        nonlocal pbar
        if total > 0:
            if pbar is None or pbar.total != total:
                if pbar:
                    pbar.close()
                pbar = tqdm(total=total, desc="Segments", unit="seg")
            pbar.n = current
            pbar.set_postfix_str(message[:40])
            pbar.refresh()
        else:
            print(message)

    try:
        # Create generator
        generator = Generator(config, progress_callback=progress_callback)

        # Run generation
        print(f"Starting generation: {config.name}")
        print(f"Source: {config.source_parquet}")
        print(f"Output: {config.output_dir}")

        result = generator.run()

        if pbar:
            pbar.close()

        print("\nGeneration complete!")
        print(f"Processed {result.success_count} books ({result.failure_count} failed)")

        # Summary statistics
        if result.records:
            total_tokens = sum(r.source_tokens for r in result.records)
            total_qa = sum(
                len([m for m in r.qa_conversation if m.get("role") == "assistant"])
                for r in result.records
            )
            print(f"Total source tokens: {total_tokens:,}")
            print(f"Total Q&A turns: {total_qa}")
        print(f"Total cost: ${result.total_cost:.4f}")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        if pbar:
            pbar.close()
        return 130
    except Exception as e:
        logger.exception("Generation failed")
        print(f"Error: {e}")
        if pbar:
            pbar.close()
        return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze a book to determine strategy."""
    setup_logging(args.verbose)

    import pandas as pd

    # Load source
    source = Path(args.source)
    if not source.exists():
        print(f"Error: Source file not found: {source}")
        return 1

    df = pd.read_parquet(source)

    # Create analyzer
    config = StrategyConfig(
        max_context_tokens=args.max_tokens,
        short_book_threshold=args.threshold,
    )
    analyzer = BookAnalyzer(config)

    if args.barcode:
        # Analyze single book
        try:
            analysis = analyzer.analyze_from_dataframe(df, args.barcode)
        except ValueError as e:
            print(f"Error: {e}")
            return 1

        print(f"Barcode: {analysis.barcode}")
        print(f"Title: {analysis.title}")
        print(f"Author: {analysis.author}")
        print(f"Characters: {analysis.char_count:,}")
        print(f"Tokens: {analysis.token_count:,}")
        print(f"Strategy: {analysis.strategy}")
        print(f"Estimated segments: {analysis.estimated_segments}")

    else:
        # Analyze all books
        analyses = analyzer.analyze_collection(df)

        print(f"Analyzed {len(analyses)} books\n")
        print(f"{'Barcode':<20} {'Tokens':>12} {'Strategy':<12} {'Segments':>8}")
        print("-" * 60)

        short_count = 0
        long_count = 0
        total_tokens = 0

        for a in sorted(analyses, key=lambda x: -x.token_count):
            print(
                f"{a.barcode:<20} {a.token_count:>12,} {a.strategy:<12} {a.estimated_segments:>8}"
            )
            total_tokens += a.token_count
            if a.strategy == "short_book":
                short_count += 1
            else:
                long_count += 1

        print("-" * 60)
        print(f"Total: {total_tokens:,} tokens")
        print(f"Short books: {short_count}, Long books: {long_count}")

    return 0


def cmd_segment(args: argparse.Namespace) -> int:
    """Preview segmentation for a book."""
    setup_logging(args.verbose)

    import pandas as pd

    # Load source
    source = Path(args.source)
    if not source.exists():
        print(f"Error: Source file not found: {source}")
        return 1

    df = pd.read_parquet(source)

    # Get book text
    matches = df[df["barcode"] == args.barcode]
    if len(matches) == 0:
        print(f"Error: Barcode {args.barcode} not found")
        return 1

    text = matches.iloc[0]["text"]
    title = matches.iloc[0].get("title", "Unknown")

    # Create segmenter
    config = StrategyConfig(
        max_context_tokens=args.max_tokens,
        segment_summary_tokens=args.segment_tokens,
    )
    segmenter = Segmenter(config)

    # Segment
    result = segmenter.segment(text)

    print(f"Book: {title}")
    print(f"Method: {result.method}")
    print(f"Total tokens: {result.total_tokens:,}")
    print(f"Segments: {len(result.segments)}\n")

    print(f"{'#':>3} {'Title':<50} {'Tokens':>10}")
    print("-" * 70)

    for seg in result.segments:
        title_display = seg.title[:47] + "..." if len(seg.title) > 50 else seg.title
        print(f"{seg.index + 1:>3} {title_display:<50} {seg.token_count:>10,}")

    if args.preview:
        print(f"\n--- Preview of segment {args.preview} ---\n")
        if 0 < args.preview <= len(result.segments):
            seg = result.segments[args.preview - 1]
            segment_text = segmenter.get_segment_text(text, seg)
            preview = segment_text[:2000]
            if len(segment_text) > 2000:
                preview += "\n... [truncated]"
            print(preview)
        else:
            print(f"Invalid segment number: {args.preview}")

    return 0


def add_generate_subparsers(subparsers: Any) -> None:
    """Add generate-related subparsers to main CLI.

    Args:
        subparsers: ArgumentParser subparsers action (from add_subparsers()).
    """

    # generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate training data from processed books",
    )
    gen_parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to YAML config file",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        help="Override output directory from config",
    )
    gen_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze books to determine generation strategy",
    )
    analyze_parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Source parquet file",
    )
    analyze_parser.add_argument(
        "--barcode",
        "-b",
        help="Analyze specific book (otherwise analyzes all)",
    )
    analyze_parser.add_argument(
        "--max-tokens",
        type=int,
        default=131000,
        help="Maximum context tokens (default: 131000)",
    )
    analyze_parser.add_argument(
        "--threshold",
        type=int,
        default=131000,
        help="Short book threshold tokens (default: 131000)",
    )
    analyze_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # segment command
    seg_parser = subparsers.add_parser(
        "segment",
        help="Preview book segmentation",
    )
    seg_parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Source parquet file",
    )
    seg_parser.add_argument(
        "--barcode",
        "-b",
        required=True,
        help="Book barcode",
    )
    seg_parser.add_argument(
        "--max-tokens",
        type=int,
        default=131000,
        help="Maximum context tokens (default: 131000)",
    )
    seg_parser.add_argument(
        "--segment-tokens",
        type=int,
        default=8000,
        help="Target tokens per segment summary (default: 8000)",
    )
    seg_parser.add_argument(
        "--preview",
        type=int,
        help="Preview text from segment N (1-indexed)",
    )
    seg_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    seg_parser.set_defaults(func=cmd_segment)
