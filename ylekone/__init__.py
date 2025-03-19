from ylekone.group_stats import GroupStats
from ylekone.stats_by_party import StatsByParty, PartyStats, MeanDifference
from ylekone.objects import (
    Constituencies,
    Constituency,
    Parties,
    Party,
    Candidates,
    Candidate,
    Questions,
    Question,
    Answers,
    Answer,
)


def Vaalikone(*args, **kwargs):
    """Backwards compatibility"""
    return Constituencies(*args, **kwargs)
