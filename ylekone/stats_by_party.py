from dataclasses import dataclass

from ylekone.group_stats import GroupStats


class StatsByParty:
    """Response statistics grouped by party"""

    def __init__(self):
        self.questions = {}
        self.parties = {}
        self.stats = {}

    def __iter__(self):
        for qid, parties in self.stats.items():
            for pid, stats in parties.items():
                question = self.questions[qid]
                party = self.parties[pid]
                yield question, party, stats

    def add(self, question, party, answer):
        if party is None:  # Esim. puolueisiin sitoutumattomat
            return
        if question.id not in self.questions:
            self.questions[question.id] = question
        if party.id not in self.parties:
            self.parties[party.id] = party
        self._get_stats(question, party).add(answer)

    def mean_differences(self, party1, party2):
        result = []
        for question, parties in self.stats.items():
            if party1 in parties and party2 in parties:
                stats1 = parties[party1]
                stats2 = parties[party2]
                delta = stats2.mean - stats1.mean
                result.append(MeanDifference(delta, question, stats1, stats2))
        return result

    def to_json(self):
        j = {}
        j["parties"] = [
            {"id": key, "name": party.name, "abbreviation": party.abbreviation}
            for key, party in self.parties.items()
        ]
        j["questions"] = [
            {"id": key, "text": question.text}
            for key, question in self.questions.items()
        ]
        j["stats"] = [
            {
                "party_id": party.id,
                "question_id": question.id,
                "answers": stats.array,
                "mean": float(stats.mean),
                "std": float(stats.std),
            }
            for question, party, stats in self
        ]
        return j

    def _get_stats(self, question, party):
        parties = self._get_parties(question)
        if party.id not in parties:
            parties[party.id] = PartyStats(question, party)
        return parties[party.id]

    def _get_parties(self, question):
        questions = self.stats
        if question.id not in questions:
            questions[question.id] = {}
        return questions[question.id]


class PartyStats(GroupStats):
    def __init__(self, question, party):
        super().__init__()
        self.question = question
        self.party = party

    def __repr__(self):
        return f"PartyStats({self.party.id}, {self.question.id}, [{', '.join(str(e) for e in self.array)}])"

    @property
    def pretty(self):
        return f"{self.party:>8} | {self.pretty_numbers}"


@dataclass
class MeanDifference:
    difference: float
    question: int
    stats1: PartyStats
    stats2: PartyStats

    @property
    def abs_difference(self):
        return abs(self.difference)

    def __lt__(self, other):
        return self.abs_difference < other.abs_difference
