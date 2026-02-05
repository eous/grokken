"""
Prompt templates for summarization and Q&A generation.

All templates use simple string formatting with named placeholders.
"""

import logging
import re

logger = logging.getLogger(__name__)

# System prompt for all summarization tasks
SUMMARIZATION_SYSTEM = """You are an expert at summarizing historical and academic texts. \
Your summaries are:
- Comprehensive: capturing main arguments, key concepts, and important details
- Structured: preserving the logical organization of the original
- Precise: using accurate terminology from the original text
- Useful: enabling readers to understand and answer questions about the content

You maintain scholarly objectivity and avoid editorializing."""


# Template for summarizing a complete short book
SHORT_BOOK_SUMMARY = """You are summarizing "{title}" by {author} ({date}).

This is a historical text of approximately {token_count:,} tokens.

Create a comprehensive summary that:
1. Captures the main thesis and central arguments
2. Preserves important names, concepts, and terminology
3. Maintains the logical structure and flow of the work
4. Includes key examples and evidence used by the author
5. Notes any significant historical or intellectual context

Your summary should enable someone to:
- Understand the book's core contribution and arguments
- Answer detailed questions about its content
- Identify its place in intellectual history

TARGET LENGTH: Approximately {target_tokens:,} tokens (be thorough but concise).

---

FULL TEXT:

{text}

---

Provide your comprehensive summary:"""


# Template for summarizing a segment with prior context
SEGMENT_SUMMARY = """You are progressively summarizing "{title}" by {author}.

This is segment {segment_index} of {total_segments}: "{segment_title}"

{context_section}

---

CURRENT SEGMENT TEXT:

{segment_text}

---

Summarize this segment, building on any previous context. Your summary should:
1. Capture the key ideas, arguments, and examples in this segment
2. Connect them to earlier material where relevant
3. Note important terminology, names, and concepts introduced
4. Preserve the logical flow and structure

TARGET LENGTH: Approximately {target_tokens:,} tokens.

Provide your summary of this segment:"""


# Template for generating the final summary from accumulated summaries
FINAL_SUMMARY_FROM_SEGMENTS = """You are creating the final summary of \
"{title}" by {author} ({date}).

You have progressively summarized {num_segments} segments of this work. \
Below are all segment summaries.

---

ACCUMULATED SEGMENT SUMMARIES:

{accumulated_summaries}

---

Create a unified, comprehensive summary of the entire work that:
1. Synthesizes the segment summaries into a coherent whole
2. Identifies the book's central thesis and main arguments
3. Traces the development of key ideas across the work
4. Preserves important terminology, names, and concepts
5. Captures the overall structure and organization
6. Enables detailed Q&A about the book's content

TARGET LENGTH: Approximately {target_tokens:,} tokens.

Provide your comprehensive summary:"""


# Template for generating follow-up Q&A
QA_GENERATION = """Based on this summary of "{title}" by {author}:

---

{summary}

---

Generate {num_questions} insightful questions that test understanding of this work.
Questions should cover:
- Main arguments and central thesis
- Key concepts and terminology
- Important details and examples
- Relationships between ideas
- Historical or intellectual significance

For each question, provide a thorough answer based ONLY on the information in the summary above.

Format your response as a numbered list with questions and answers:

1. **Question:** [Your question]
   **Answer:** [Your detailed answer]

2. **Question:** [Your question]
   **Answer:** [Your detailed answer]

(Continue for all {num_questions} questions)"""


def format_short_book_prompt(
    title: str,
    author: str,
    date: str,
    text: str,
    token_count: int,
    target_tokens: int = 16000,
) -> tuple[str, str]:
    """
    Format prompt for short book summarization.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    prompt = SHORT_BOOK_SUMMARY.format(
        title=title,
        author=author,
        date=date,
        text=text,
        token_count=token_count,
        target_tokens=target_tokens,
    )
    return SUMMARIZATION_SYSTEM, prompt


def format_segment_prompt(
    title: str,
    author: str,
    segment_index: int,
    total_segments: int,
    segment_title: str,
    segment_text: str,
    accumulated_summaries: str | None = None,
    target_tokens: int = 8000,
) -> tuple[str, str]:
    """
    Format prompt for segment summarization.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    if accumulated_summaries:
        context_section = f"""PREVIOUS CONTEXT (summaries of segments 1-{segment_index}):

{accumulated_summaries}"""
    else:
        context_section = "(This is the first segment - no previous context)"

    prompt = SEGMENT_SUMMARY.format(
        title=title,
        author=author,
        segment_index=segment_index + 1,  # 1-indexed for display
        total_segments=total_segments,
        segment_title=segment_title,
        context_section=context_section,
        segment_text=segment_text,
        target_tokens=target_tokens,
    )
    return SUMMARIZATION_SYSTEM, prompt


def format_final_summary_prompt(
    title: str,
    author: str,
    date: str,
    accumulated_summaries: str,
    num_segments: int,
    target_tokens: int = 16000,
) -> tuple[str, str]:
    """
    Format prompt for final summary synthesis.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    prompt = FINAL_SUMMARY_FROM_SEGMENTS.format(
        title=title,
        author=author,
        date=date,
        accumulated_summaries=accumulated_summaries,
        num_segments=num_segments,
        target_tokens=target_tokens,
    )
    return SUMMARIZATION_SYSTEM, prompt


def format_qa_prompt(
    title: str,
    author: str,
    summary: str,
    num_questions: int = 5,
) -> tuple[str, str]:
    """
    Format prompt for Q&A generation.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system = """You are an expert at creating educational questions that test \
deep understanding of texts. Your questions are insightful, varied in difficulty, \
and your answers are thorough and accurate."""

    prompt = QA_GENERATION.format(
        title=title,
        author=author,
        summary=summary,
        num_questions=num_questions,
    )
    return system, prompt


def parse_qa_response(response: str) -> list[tuple[str, str]]:
    """
    Parse Q&A response into list of (question, answer) tuples.

    Handles various formatting styles from LLM responses.

    Args:
        response: Raw LLM response text containing Q&A pairs.

    Returns:
        List of (question, answer) tuples. Empty list if parsing fails.
    """
    if not response or not response.strip():
        logger.warning("Empty response provided to parse_qa_response")
        return []

    qa_pairs = []

    # Pattern 1: Numbered Q&A with **Question:** and **Answer:** format (preferred)
    pattern_markdown = (
        r"\d+\.\s*\*\*Question:\*\*\s*(.+?)\s*\*\*Answer:\*\*\s*(.+?)"
        r"(?=\d+\.\s*\*\*Question:|$)"
    )
    matches = re.findall(pattern_markdown, response, re.DOTALL)

    if matches:
        logger.debug(f"Parsed {len(matches)} Q&A pairs using markdown pattern")
        return [(q.strip(), a.strip()) for q, a in matches]

    # Pattern 2: Q: ... A: ... format
    pattern_qa_prefix = (
        r"(?:Q:|Question:)\s*(.+?)\s*(?:A:|Answer:)\s*(.+?)"
        r"(?=(?:Q:|Question:)|$)"
    )
    matches = re.findall(pattern_qa_prefix, response, re.DOTALL | re.IGNORECASE)

    if matches:
        logger.debug(f"Parsed {len(matches)} Q&A pairs using Q:/A: pattern")
        return [(q.strip(), a.strip()) for q, a in matches]

    # Pattern 3: Fallback - numbered list with questions followed by answers
    logger.debug("Primary patterns failed, attempting fallback parsing")
    lines = response.strip().split("\n")
    current_q = None
    current_a: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this looks like a new question (starts with number or "Question")
        if re.match(r"^\d+[\.\)]\s*", line) or line.lower().startswith("question"):
            if current_q and current_a:
                qa_pairs.append((current_q, " ".join(current_a)))
            current_q = re.sub(r"^\d+[\.\)]\s*", "", line)
            current_q = re.sub(r"^(?:Question:?\s*)", "", current_q, flags=re.IGNORECASE)
            current_a = []
        elif current_q is not None:
            # This is part of the answer
            current_a.append(line)

    if current_q and current_a:
        qa_pairs.append((current_q, " ".join(current_a)))

    if qa_pairs:
        logger.debug(f"Parsed {len(qa_pairs)} Q&A pairs using fallback pattern")
    else:
        logger.warning(
            f"Failed to parse any Q&A pairs from response "
            f"(length: {len(response)} chars, preview: {response[:100]!r}...)"
        )

    return qa_pairs
