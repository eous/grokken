"""
The Principia 34 collection.

34 exceptional foundational works from the Institutional Books dataset
with significance score >= 36.

Named after Newton's Principia and the pattern of titles featuring
"Principles", "Elements", and "Introduction".
"""

# Import all book handlers to register them
from grokken.books.principia.psychology_james import PrinciplesPsychology

__all__ = ["PrinciplesPsychology"]
