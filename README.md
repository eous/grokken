# grokken

> *"To understand so thoroughly that the observer becomes part of the observed."*

Deep understanding and transformation of historical texts for training data.

## What is this?

`grokken` is a pipeline for processing OCR'd historical books into clean, structured training data. It handles the messy reality of 19th-century texts: encoding issues, OCR artifacts, archaic typography, and inconsistent formatting.

## Core Concepts

- **BookProcessor**: Base class for book-specific processing logic
- **Transforms**: Composable functions for text cleanup (encoding, OCR, typography, structure)
- **Registry**: Auto-discovers book handlers for batch processing

## Project Structure

```
grokken/
├── grokken/
│   ├── base.py          # BookProcessor base class
│   ├── registry.py      # Handler discovery
│   ├── cli.py           # Command-line interface
│   ├── transforms/      # Reusable transform library
│   ├── outputs/         # Output formatters (parquet, jsonl)
│   └── books/           # Book-specific handlers
│       └── principia/   # The Principia 34 collection
├── data/
│   ├── raw/             # Input data (symlinked)
│   └── processed/       # Output data
└── tests/
```

## Usage

```bash
# Process a single book
grokken process --barcode 32044010149714

# Process all books in a collection
grokken process --collection principia

# List available handlers
grokken list
```

## The Principia 34

Our initial collection: 34 exceptional foundational works (score >= 36) from the Institutional Books dataset, including:

- William James's *Principles of Psychology* (1890)
- John Stuart Mill's *Principles of Political Economy* (1884)
- Herbert Spencer's *Principles of Sociology* (1895)
- The Federalist Papers (1864 reprint)

## Etymology

**grokken** (v.): The past participle of *grok* that Heinlein never wrote.

"The text has been grokken" — it has been understood so deeply that its essence can be extracted and transformed.
