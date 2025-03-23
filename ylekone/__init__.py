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
from ylekone.public_api import PublicApi


def av25():
    return Constituencies(PublicApi.av25())


def kv25():
    return Constituencies(PublicApi.kv25())
