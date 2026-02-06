"""
Simulated User - Generates intelligent follow-up questions for book summaries.

Produces varied, contextual questions that test deep understanding of
the summarized content using different questioning styles.
"""

import logging
import random

from grokken.generation.providers.base import LLMProvider

logger = logging.getLogger(__name__)


# Follow-up question styles for book comprehension
FOLLOWUP_STYLES = [
    "comprehension",  # Test basic understanding of main ideas
    "analysis",  # Probe deeper analytical thinking
    "synthesis",  # Connect ideas across sections
    "evaluation",  # Judge arguments or compare perspectives
    "application",  # Apply concepts to new contexts
    "clarification",  # Seek explanation of complex points
]


# Style-specific instructions for generating questions
STYLE_PROMPTS = {
    "comprehension": """STYLE: Test basic comprehension of main ideas

VARIATION PATTERNS (pick ONE approach):
- Main thesis (~30%): "What is the author's central argument about X?"
- Key concept (~25%): "How does the author define X?"
- Summary (~25%): "What are the main points in the section about X?"
- Factual recall (~20%): "According to the text, what causes X?"

Focus on testing whether the reader grasped the fundamental ideas.
OUTPUT: A single clear question (1-2 sentences).""",
    "analysis": """STYLE: Probe deeper analytical understanding

VARIATION PATTERNS (pick ONE approach):
- Reasoning (~30%): "Why does the author argue that X leads to Y?"
- Evidence (~25%): "What evidence does the author provide for X?"
- Structure (~25%): "How does the author's treatment of X support the overall thesis?"
- Assumptions (~20%): "What assumptions underlie the author's claim about X?"

Target the logical structure and reasoning within the text.
OUTPUT: A single analytical question (1-2 sentences).""",
    "synthesis": """STYLE: Connect ideas across different parts of the work

VARIATION PATTERNS (pick ONE approach):
- Cross-reference (~35%): "How does the author's discussion of X \
relate to the earlier treatment of Y?"
- Theme connection (~30%): "What common thread connects the author's views on X and Y?"
- Development (~20%): "How does the concept of X evolve throughout the work?"
- Integration (~15%): "How do X and Y together support the author's main argument?"

Require connecting multiple sections or concepts.
OUTPUT: A single synthesis question (1-2 sentences).""",
    "evaluation": """STYLE: Judge arguments or compare perspectives

VARIATION PATTERNS (pick ONE approach):
- Critique (~30%): "What are the potential weaknesses in the author's argument about X?"
- Comparison (~25%): "How does this view of X compare to alternative perspectives?"
- Significance (~25%): "Why is the author's contribution to understanding X important?"
- Contemporary relevance (~20%): "How might the author's views on X apply to modern contexts?"

Require critical thinking and evaluation.
OUTPUT: A single evaluative question (1-2 sentences).""",
    "application": """STYLE: Apply concepts to new contexts or examples

VARIATION PATTERNS (pick ONE approach):
- New example (~35%): "How would the author's framework explain X?"
- Practical use (~25%): "How might one apply the author's principles about X?"
- Extension (~25%): "What would the author likely say about X?"
- Prediction (~15%): "Based on the author's theory, what would happen if X?"

Test ability to use the concepts beyond the text.
OUTPUT: A single application question (1-2 sentences).""",
    "clarification": """STYLE: Seek explanation of complex or ambiguous points

VARIATION PATTERNS (pick ONE approach):
- Terminology (~30%): "What exactly does the author mean by X in this context?"
- Distinction (~25%): "How does the author distinguish between X and Y?"
- Elaboration (~25%): "Can you explain the author's reasoning about X in more detail?"
- Resolution (~20%): "How does the author reconcile X with Y?"

Target complex aspects that benefit from explanation.
OUTPUT: A single clarification question (1-2 sentences).""",
}


# Style constraints applied to all generation prompts to suppress LLM verbal tics.
# These patterns are characteristic of RLHF-trained models and contaminate training data.
STYLE_CONSTRAINTS = """
WRITING STYLE — MANDATORY:
- Write in plain, direct academic prose. No filler phrases or verbal tics.
- NEVER use these words/phrases: "genuinely", "fascinating", "brilliant", "elegant", \
"penetrating", "remarkably", "strikingly", "compelling", "profound", "nuanced", \
"insightful", "sophisticated", "absolutely", "crucially", "notably", "interestingly", \
"it's worth noting", "great question", "good question", "delve", "unpack", "dive into", \
"dive deeper", "at its core", "gets at", "grapple with", "wrestle with", "the heart of", \
"cuts to the heart", "tease out", "tease apart", "let me".
- NEVER validate or praise the question ("That's a great question", "You've identified \
a real tension", "This is precisely the right question"). Just answer it.
- NEVER use the pattern "This is a genuinely/really [adjective] question/point/observation".
- Prefer concrete and specific language over abstract evaluative language.
- Start answers by engaging directly with the substance, not with meta-commentary about \
the question's quality."""

# Persona definition for the simulated reader, structured around concrete behavioral
# traits rather than vague archetypes. Inspired by contrastive persona prompting
# (Lu et al., "The Assistant Axis", 2025) — specifying where on key trait axes the
# persona should sit prevents drift toward the model's default assistant mode.
SIMULATED_USER_SYSTEM = """You are playing the role of Alex, a second-year PhD student in \
philosophy of mind who is working through a major historical text for a qualifying exam.

PERSONALITY TRAITS:
- Analytical and methodical: you break arguments into premises and test each one
- Direct and concise: you ask questions in 1-3 sentences, no preamble or throat-clearing
- Skeptical but fair: you look for weaknesses in arguments without being dismissive
- Understated: you don't perform enthusiasm or use superlatives
- Focused: you care about what the text actually says, not about being impressive

BEHAVIORAL RULES:
- Ask your question immediately. Never open with commentary on previous answers.
- Never praise or evaluate the quality of an answer ("That's a great point", \
"What a compelling analysis"). Just ask your next question.
- Frame questions around specific claims, distinctions, or arguments in the text.
- When you disagree or see a problem, state it plainly: "But doesn't that contradict..." \
or "I don't see how X follows from Y."
- You sometimes push back on answers: "Wait, that doesn't address..." or "But earlier \
you said..."
- Your tone is collegial but businesslike — like talking to a study partner, not a professor.

OUTPUT: A single question (1-3 sentences). Nothing else."""


# Stop reasons that indicate truncation (provider-specific)
_TRUNCATION_STOP_REASONS = {"max_tokens", "length"}


class SimulatedUser:
    """Generates intelligent follow-up questions based on book summaries."""

    def __init__(self, provider: LLMProvider):
        """
        Initialize the simulated user.

        Args:
            provider: LLM provider for generating questions.
        """
        self.provider = provider

    def _build_prompt(
        self,
        title: str,
        author: str,
        summary: str,
        style: str,
        previous_questions: list[str] | None = None,
    ) -> str:
        """Build the prompt for generating a follow-up question."""
        style_instruction = STYLE_PROMPTS.get(style, STYLE_PROMPTS["comprehension"])

        # Include previous questions to avoid repetition
        prev_text = ""
        if previous_questions:
            prev_list = "\n".join(f"- {q}" for q in previous_questions)
            prev_text = f"""
QUESTIONS ALREADY ASKED (avoid repeating these topics):
{prev_list}
"""

        return f"""{style_instruction}

BOOK: "{title}" by {author}

SUMMARY:
{summary}
{prev_text}
Generate a single, thoughtful question that a curious reader might ask after reading this summary. \
The question should be specific to the content and naturally phrased.

Respond with ONLY the question, nothing else."""

    def generate_question(
        self,
        title: str,
        author: str,
        summary: str,
        style: str = "comprehension",
        previous_questions: list[str] | None = None,
        temperature: float = 0.8,
    ) -> dict:
        """
        Generate a follow-up question based on the summary.

        Args:
            title: Book title.
            author: Book author.
            summary: The book summary to question.
            style: Question style (comprehension, analysis, etc.).
            previous_questions: Previously asked questions to avoid repetition.
            temperature: Sampling temperature for variety.

        Returns:
            Dict with keys: question, style, success, error
        """
        if not summary or not summary.strip():
            return {
                "question": "",
                "style": style,
                "success": False,
                "error": "Empty summary",
            }

        try:
            prompt = self._build_prompt(
                title=title,
                author=author,
                summary=summary,
                style=style,
                previous_questions=previous_questions,
            )

            result = self.provider.generate(
                prompt=prompt,
                system=SIMULATED_USER_SYSTEM,
                temperature=temperature,
                max_tokens=4096,
            )

            if result.finish_reason in _TRUNCATION_STOP_REASONS:
                return {
                    "question": "",
                    "style": style,
                    "success": False,
                    "error": f"Question truncated (finish_reason={result.finish_reason})",
                }

            question = result.text.strip().strip("\"'")

            if not question or len(question) < 10:
                return {
                    "question": "",
                    "style": style,
                    "success": False,
                    "error": "Generated question too short",
                }

            logger.debug(f"Generated {style} question: {question[:100]}...")
            return {
                "question": question,
                "style": style,
                "success": True,
                "error": None,
                # Include prompts for training data
                "system_prompt": SIMULATED_USER_SYSTEM,
                "user_prompt": prompt,
            }

        except Exception as e:
            logger.warning(f"Question generation failed: {e}")
            return {
                "question": "",
                "style": style,
                "success": False,
                "error": str(e),
                "system_prompt": "",
                "user_prompt": "",
            }

    def generate_answer(
        self,
        title: str,
        author: str,
        summary: str,
        question: str,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate an answer to a question based on the summary.

        Args:
            title: Book title.
            author: Book author.
            summary: The book summary.
            question: The question to answer.
            temperature: Sampling temperature.

        Returns:
            Dict with keys: answer, success, error
        """
        try:
            prompt = f"""Based on this summary of "{title}" by {author}:

{summary}

---

Question: {question}

Provide a thorough, accurate answer based ONLY on the information in the summary above. \
If the summary doesn't contain enough information to fully answer, acknowledge this \
while providing what can be determined.

Answer:"""

            system = f"""You are a knowledgeable study partner answering questions about a book \
based on its summary. Your answers are thorough, well-organized, and cite specific \
details from the summary. You answer the way a well-prepared colleague would — directly \
and precisely, without filler or flattery.
{STYLE_CONSTRAINTS}"""

            result = self.provider.generate(
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=16384,
            )

            if result.finish_reason in _TRUNCATION_STOP_REASONS:
                return {
                    "answer": "",
                    "success": False,
                    "error": f"Answer truncated (finish_reason={result.finish_reason})",
                }

            answer = result.text.strip()

            if not answer or len(answer) < 20:
                return {
                    "answer": "",
                    "success": False,
                    "error": "Generated answer too short",
                }

            return {
                "answer": answer,
                "success": True,
                "error": None,
                # Include prompts for training data
                "system_prompt": system,
                "user_prompt": prompt,
            }

        except Exception as e:
            logger.warning(f"Answer generation failed: {e}")
            return {
                "answer": "",
                "success": False,
                "error": str(e),
                "system_prompt": "",
                "user_prompt": "",
            }

    def generate_qa_turns(
        self,
        title: str,
        author: str,
        summary: str,
        num_turns: int = 5,
        styles: list[str] | None = None,
        temperature: float = 0.8,
    ) -> list[dict]:
        """
        Generate multiple Q&A turns with varied styles.

        Args:
            title: Book title.
            author: Book author.
            summary: The book summary.
            num_turns: Number of Q&A turns to generate.
            styles: Specific styles to use (cycles through if fewer than num_turns).
                   If None, uses varied selection from FOLLOWUP_STYLES.
            temperature: Sampling temperature.

        Returns:
            List of dicts with keys: question, answer, style, turn_number, success
        """
        if styles is None:
            # Use a thread-local random instance for thread safety
            rng = random.Random()
            # Use a varied selection of styles
            styles = rng.sample(FOLLOWUP_STYLES, min(num_turns, len(FOLLOWUP_STYLES)))
            # If we need more turns than styles, cycle through
            while len(styles) < num_turns:
                remaining = min(num_turns - len(styles), len(FOLLOWUP_STYLES))
                styles.extend(rng.sample(FOLLOWUP_STYLES, remaining))

        qa_turns = []
        previous_questions = []

        for i in range(num_turns):
            style = styles[i % len(styles)]

            # Generate question
            q_result = self.generate_question(
                title=title,
                author=author,
                summary=summary,
                style=style,
                previous_questions=previous_questions,
                temperature=temperature,
            )

            if not q_result["success"]:
                logger.warning(f"Failed to generate question {i + 1}: {q_result['error']}")
                continue

            question = q_result["question"]
            previous_questions.append(question)

            # Generate answer
            a_result = self.generate_answer(
                title=title,
                author=author,
                summary=summary,
                question=question,
                temperature=max(0.0, temperature - 0.1),  # Slightly lower temp for answers
            )

            if not a_result["success"]:
                logger.warning(f"Failed to generate answer {i + 1}: {a_result['error']}")
                continue

            qa_turns.append(
                {
                    "question": question,
                    "answer": a_result["answer"],
                    "style": style,
                    "turn_number": len(qa_turns) + 1,
                    "success": True,
                    # Include prompts for training data
                    "question_system_prompt": q_result.get("system_prompt", ""),
                    "question_user_prompt": q_result.get("user_prompt", ""),
                    "answer_system_prompt": a_result.get("system_prompt", ""),
                    "answer_user_prompt": a_result.get("user_prompt", ""),
                }
            )

        return qa_turns

    def _trim_conversation(
        self,
        conversation: list[dict],
        max_chars: int = 320000,
    ) -> list[dict]:
        """
        Trim conversation to stay within approximate token budget.

        Keeps the system message and most recent messages. Drops oldest
        user+assistant pairs from the middle when over budget.

        Args:
            conversation: Full conversation list.
            max_chars: Max total characters (~80k tokens at 4 chars/token).

        Returns:
            Trimmed conversation (may be the same list if under budget).
        """
        total_chars = sum(len(m.get("content", "")) for m in conversation)
        if total_chars <= max_chars:
            return conversation

        # Keep system message (index 0) and trim from the front of the rest
        system_msg = (
            conversation[0] if conversation and conversation[0]["role"] == "system" else None
        )
        rest = conversation[1:] if system_msg else conversation[:]

        # Drop pairs from the front until under budget
        while len(rest) >= 2:
            rest_chars = sum(len(m.get("content", "")) for m in rest)
            system_chars = len(system_msg["content"]) if system_msg else 0
            if rest_chars + system_chars <= max_chars:
                break
            # Drop oldest pair (user + assistant)
            if len(rest) >= 2 and rest[0]["role"] == "user" and rest[1]["role"] == "assistant":
                rest = rest[2:]
            else:
                rest = rest[1:]

        if system_msg:
            return [system_msg] + rest
        return rest

    def generate_multiturn_qa(
        self,
        title: str,
        author: str,
        segment_summaries: list[dict],
        turns_per_segment: int = 2,
        temperature: float = 0.8,
    ) -> list[dict]:
        """
        Generate a multi-turn Q&A conversation across all segment summaries.

        This creates one cohesive conversation where a curious reader progresses
        through the book, asking questions that build on previous answers and
        connect ideas across chapters.

        Args:
            title: Book title.
            author: Book author.
            segment_summaries: List of dicts with 'title' and 'summary' keys.
            turns_per_segment: Number of Q&A turns per segment (default 2).
            temperature: Sampling temperature.

        Returns:
            List of conversation messages: [{role: str, content: str}, ...]
        """
        if not segment_summaries:
            logger.warning("No segment summaries provided for multi-turn Q&A")
            return []

        conversation: list[dict] = []

        # System message
        system_content = MULTITURN_QA_SYSTEM.format(title=title, author=author)
        conversation.append({"role": "system", "content": system_content})

        # Track styles used to ensure variety
        rng = random.Random()
        available_styles = list(FOLLOWUP_STYLES)

        total_turns = 0
        num_segments = len(segment_summaries)

        for seg_idx, segment in enumerate(segment_summaries):
            seg_title = segment.get("title", f"Segment {seg_idx + 1}")
            seg_summary = segment.get("summary", "")

            if not seg_summary:
                logger.warning(f"Empty summary for segment {seg_idx}, skipping")
                continue

            # Generate Q&A turns for this segment
            for turn in range(turns_per_segment):
                total_turns += 1

                # Determine question style (progress from comprehension to synthesis)
                if turn == 0 and seg_idx == 0:
                    style = "comprehension"
                elif seg_idx > 0 and turn == 0 and rng.random() < 0.4:
                    style = "synthesis"  # Cross-segment questions at segment boundaries
                else:
                    style = rng.choice(available_styles)

                # Determine if this should reference earlier content
                should_cross_reference = seg_idx > 0 and turn == 0 and rng.random() < 0.5

                # Build context for question generation
                if turn == 0:
                    # First turn of segment: include the new summary
                    new_segment_context = f"""NEW CHAPTER SUMMARY - "{seg_title}":

{seg_summary}

This is chapter {seg_idx + 1} of {num_segments}."""
                else:
                    new_segment_context = "(Continue discussing the current chapter)"

                cross_ref_instruction = (
                    CROSS_REFERENCE_INSTRUCTIONS[1]
                    if should_cross_reference
                    else CROSS_REFERENCE_INSTRUCTIONS[0]
                )

                # Generate question
                question = self._generate_multiturn_question(
                    title=title,
                    author=author,
                    conversation=conversation,
                    new_segment_context=new_segment_context,
                    style=style,
                    cross_reference_instruction=cross_ref_instruction,
                    temperature=temperature,
                )

                if not question:
                    logger.warning(
                        f"Failed to generate question for segment {seg_idx}, turn {turn}"
                    )
                    continue

                # Add user message (with segment summary on first turn)
                if turn == 0:
                    user_content = f"""Here's a summary of {seg_title}:

{seg_summary}

{question}"""
                else:
                    user_content = question

                conversation.append({"role": "user", "content": user_content})

                # Generate answer
                answer = self._generate_multiturn_answer(
                    title=title,
                    author=author,
                    conversation=conversation,
                    temperature=max(0.0, temperature - 0.1),
                )

                if not answer:
                    logger.warning(f"Failed to generate answer for segment {seg_idx}, turn {turn}")
                    # Remove the unanswered question
                    conversation.pop()
                    continue

                conversation.append({"role": "assistant", "content": answer})

        # Final synthesis question about the whole book
        if len(segment_summaries) > 1:
            synthesis_question = self._generate_synthesis_question(
                title=title,
                author=author,
                conversation=conversation,
                temperature=temperature,
            )

            if synthesis_question:
                conversation.append({"role": "user", "content": synthesis_question})

                final_answer = self._generate_multiturn_answer(
                    title=title,
                    author=author,
                    conversation=conversation,
                    temperature=temperature - 0.1,
                )

                if final_answer:
                    conversation.append({"role": "assistant", "content": final_answer})
                else:
                    conversation.pop()  # Remove unanswered question

        logger.info(
            f"Generated multi-turn Q&A: {len(conversation)} messages "
            f"({total_turns} Q&A turns across {num_segments} segments)"
        )

        return conversation

    def _generate_multiturn_question(
        self,
        title: str,
        author: str,
        conversation: list[dict],
        new_segment_context: str,
        style: str,
        cross_reference_instruction: str,
        temperature: float,
    ) -> str | None:
        """Generate a question for multi-turn conversation."""
        # Format conversation history (exclude system message)
        history_messages = conversation[1:]  # Skip system
        if len(history_messages) > 10:
            # Truncate to recent context if very long
            history_messages = history_messages[-10:]

        history_text = (
            "\n\n".join(
                f"{'Reader' if m['role'] == 'user' else 'Assistant'}: {m['content'][:500]}..."
                if len(m["content"]) > 500
                else f"{'Reader' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in history_messages
            )
            if history_messages
            else "(This is the start of the conversation)"
        )

        style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["comprehension"])

        prompt = MULTITURN_QUESTION_PROMPT.format(
            title=title,
            author=author,
            conversation_history=history_text,
            new_segment_context=new_segment_context,
            style_instruction=style_instruction,
            cross_reference_instruction=cross_reference_instruction,
        )

        try:
            result = self.provider.generate(
                prompt=prompt,
                system=SIMULATED_USER_SYSTEM,
                temperature=temperature,
                max_tokens=4096,
            )
            if result.finish_reason in _TRUNCATION_STOP_REASONS:
                logger.warning(
                    "Multi-turn question truncated (finish_reason=%s)", result.finish_reason
                )
                return None
            question = result.text.strip().strip("\"'")
            if question and len(question) >= 10:
                return question
        except Exception as e:
            logger.warning(f"Question generation failed: {e}")

        return None

    def _generate_multiturn_answer(
        self,
        title: str,
        author: str,
        conversation: list[dict],
        temperature: float,
    ) -> str | None:
        """Generate an answer in multi-turn conversation context."""
        # The conversation already contains the question as the last user message
        # We send the full conversation to get a contextual answer

        # Trim conversation to fit within context window before sending
        trimmed = self._trim_conversation(conversation)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in trimmed]

        try:
            result = self.provider.generate_chat(
                messages=messages,
                temperature=temperature,
                max_tokens=16384,
            )
            if result.finish_reason in _TRUNCATION_STOP_REASONS:
                logger.warning(
                    "Multi-turn answer truncated (finish_reason=%s)", result.finish_reason
                )
                return None
            answer = result.text.strip()
            if answer and len(answer) >= 20:
                return answer
        except AttributeError:
            # Fallback if provider doesn't have generate_chat
            # Extract context and use single-turn generation
            system_msg = conversation[0]["content"] if conversation else ""
            # Get all summaries mentioned in user messages
            context_parts = []
            last_question = ""
            for msg in conversation[1:]:
                if msg["role"] == "user":
                    last_question = msg["content"]
                    # Check if this contains a summary
                    if "summary of" in msg["content"].lower():
                        context_parts.append(msg["content"])

            prompt = f"""Context from our conversation about "{title}" by {author}:

{chr(10).join(context_parts[-3:])}

Current question: {last_question}

Provide a thorough answer based on the summaries shared in our conversation."""

            try:
                result = self.provider.generate(
                    prompt=prompt,
                    system=system_msg,
                    temperature=temperature,
                    max_tokens=16384,
                )
                if result.finish_reason in _TRUNCATION_STOP_REASONS:
                    logger.warning(
                        "Fallback answer truncated (finish_reason=%s)", result.finish_reason
                    )
                    return None
                answer = result.text.strip()
                if answer and len(answer) >= 20:
                    return answer
            except Exception as e:
                logger.warning(f"Answer generation failed: {e}")

        except Exception as e:
            logger.warning(f"Answer generation failed: {e}")

        return None

    def _generate_synthesis_question(
        self,
        title: str,
        author: str,
        conversation: list[dict],
        temperature: float,
    ) -> str | None:
        """Generate a final synthesis question about the whole book."""
        prompt = f"""You are Alex, a PhD student who has just finished working through \
all chapters of "{title}" by {author}. You want to ask one final big-picture question.

Generate a synthesis question that:
1. Asks about the book's overall argument, contribution, or internal consistency
2. Connects threads across multiple chapters
3. Is specific enough to have a substantive answer (not just "what did you think?")

Examples:
- "Looking at the full arc from [early chapter topic] to [late chapter topic], does \
[Author]'s overall framework hold together, or are there unresolved contradictions?"
- "What would [Author] say to [specific counterargument] given the positions laid out \
across these chapters?"

Respond with ONLY the question (1-3 sentences), nothing else."""

        try:
            result = self.provider.generate(
                prompt=prompt,
                system=SIMULATED_USER_SYSTEM,
                temperature=temperature,
                max_tokens=4096,
            )
            if result.finish_reason in _TRUNCATION_STOP_REASONS:
                logger.warning(
                    "Synthesis question truncated (finish_reason=%s)", result.finish_reason
                )
                return None
            question = result.text.strip().strip("\"'")
            if question and len(question) >= 10:
                return question
        except Exception as e:
            logger.warning(f"Synthesis question generation failed: {e}")

        return None


def get_followup_style(index: int) -> str:
    """
    Get a follow-up style by index (cycles through styles).

    Args:
        index: Zero-based index.

    Returns:
        Style name string.
    """
    return FOLLOWUP_STYLES[index % len(FOLLOWUP_STYLES)]


# System prompt for multi-turn Q&A conversation
MULTITURN_QA_SYSTEM = (
    """You are a study partner helping a PhD student work through "{title}" by {author}.

The student will share chapter summaries and ask questions. Your role is to:
1. Answer questions accurately based on the summaries provided
2. Connect ideas across chapters when relevant
3. Be thorough but concise — give the substance without padding
4. Acknowledge when information isn't available in the summaries
5. When the student pushes back or challenges a point, engage with the \
substance of their objection rather than deflecting

You are peers. Do not be deferential or performatively enthusiastic. \
Answer the way a knowledgeable colleague would — directly and precisely.
"""
    + STYLE_CONSTRAINTS
)


# Prompt for generating questions in multi-turn context
MULTITURN_QUESTION_PROMPT = """You are Alex, a second-year philosophy PhD student discussing \
"{title}" by {author} with a study partner.

CONVERSATION SO FAR:
{conversation_history}

{new_segment_context}

INSTRUCTION: As Alex, generate your next question. Remember:
- You are direct and analytical — ask the question immediately, no preamble
- {style_instruction}
- {cross_reference_instruction}
- Never comment on the quality of previous answers. Just ask what you want to know next.
- If something in the previous answer was unclear or seems wrong, push back plainly.

Respond with ONLY the question (1-3 sentences), nothing else."""


STYLE_INSTRUCTIONS = {
    "comprehension": "Test basic understanding of main ideas or concepts",
    "analysis": "Probe deeper into reasoning, evidence, or logical structure",
    "synthesis": "Connect ideas across different parts or chapters",
    "evaluation": "Critically assess arguments or compare perspectives",
    "application": "Apply concepts to new contexts or examples",
    "clarification": "Seek explanation of complex or ambiguous points",
}


CROSS_REFERENCE_INSTRUCTIONS = [
    "Build naturally on what was just discussed",
    "Reference something from an earlier chapter in the conversation",
    "Ask about how this connects to previously discussed material",
    "Explore a new aspect of the current chapter",
]
