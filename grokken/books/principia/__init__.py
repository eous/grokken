"""
The Principia 34 collection.

34 exceptional foundational works from the Institutional Books dataset
with significance score >= 36.

Named after Newton's Principia and the pattern of titles featuring
"Principles", "Elements", and "Introduction".
"""

# Import all book handlers to register them
from grokken.books.principia.algebra_day import AlgebraDay
from grokken.books.principia.animal_histology_dahlgren import AnimalHistology
from grokken.books.principia.atonement import Atonement
from grokken.books.principia.bible_literature_wood import BibleAsLiterature
from grokken.books.principia.channing_works import ChanningWorks
from grokken.books.principia.chaucer_student import StudentChaucer
from grokken.books.principia.church_building_cram import ChurchBuilding
from grokken.books.principia.cornerstone_abbott import Cornerstone
from grokken.books.principia.dickens_works import DickensWorks
from grokken.books.principia.doctrines_friends_bates import DoctrinesOfFriends
from grokken.books.principia.english_literature_shaw import EnglishLiterature
from grokken.books.principia.ethics_jouffroy import IntroductionToEthics
from grokken.books.principia.evolution_conn import EvolutionToday
from grokken.books.principia.federalist import Federalist
from grokken.books.principia.hermeneutical_manual_fairbairn import HermeneuticalManual
from grokken.books.principia.history_religions_toy import HistoryOfReligions
from grokken.books.principia.international_law_davis_1900 import InternationalLawDavis1900
from grokken.books.principia.international_law_davis_1903 import InternationalLawDavis1903
from grokken.books.principia.international_law_woolsey import InternationalLawWoolsey
from grokken.books.principia.logical_theory_dewey import LogicalTheory
from grokken.books.principia.middle_ages_emerton import MiddleAges
from grokken.books.principia.natural_philosophy_comstock import NaturalPhilosophy
from grokken.books.principia.parliamentary_practice_cushing import ParliamentaryPractice
from grokken.books.principia.pathologic_histology_mallory import PathologicHistology
from grokken.books.principia.poetical_works_whittier import WhittierPoetry
from grokken.books.principia.political_economy_bowen import PoliticalEconomyBowen
from grokken.books.principia.political_economy_mill_1870 import PoliticalEconomyMill1870
from grokken.books.principia.political_economy_mill_1884 import PoliticalEconomyMill1884
from grokken.books.principia.political_science_leacock import PoliticalScience
from grokken.books.principia.psychology_james import PrinciplesPsychology
from grokken.books.principia.sociology_giddings import SociologyGiddings
from grokken.books.principia.sociology_spencer import SociologySpencer
from grokken.books.principia.stowe_writings import StoweWritings
from grokken.books.principia.vicarious_sacrifice_bushnell import VicariousSacrifice

__all__ = [
    "PrinciplesPsychology",
    "Atonement",
    "HistoryOfReligions",
    "DickensWorks",
    "StoweWritings",
    "PathologicHistology",
    "ChanningWorks",
    "AnimalHistology",
    "IntroductionToEthics",
    "PoliticalScience",
    "PoliticalEconomyMill1884",
    "DoctrinesOfFriends",
    "PoliticalEconomyMill1870",
    "WhittierPoetry",
    "ParliamentaryPractice",
    "SociologySpencer",
    "InternationalLawDavis1900",
    "InternationalLawWoolsey",
    "EnglishLiterature",
    "InternationalLawDavis1903",
    "AlgebraDay",
    "VicariousSacrifice",
    "StudentChaucer",
    "LogicalTheory",
    "ChurchBuilding",
    "HermeneuticalManual",
    "MiddleAges",
    "BibleAsLiterature",
    "EvolutionToday",
    "NaturalPhilosophy",
    "PoliticalEconomyBowen",
    "Cornerstone",
    "Federalist",
    "SociologyGiddings",
]
