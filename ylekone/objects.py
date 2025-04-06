from ylekone.public_api import PublicApi
from ylekone.stats_by_party import StatsByParty


class _Container:
    def __init__(self, api: PublicApi):
        self.api = api
        self._id_to_item = {}

    def name_to_id(self, name: str):
        del name

    def _get_by_name_or_id(self, key: int, create):
        if isinstance(key, str):
            return self._get_by_id(self.name_to_id(key), create)
        return self._get_by_id(key, create)

    def _get_by_id(self, key: int | None, create):
        if key is None:
            return None
        if key not in self._id_to_item:
            item = create(self, key)
            if item is None:
                return None
            self._id_to_item[key] = item
        return self._id_to_item[key]


class Constituencies(_Container):
    def __init__(self, api: PublicApi):
        self.api = api
        super().__init__(api)
        self.j = self.api.constituencies()
        self._name_to_id = {j["name_fi"]: j["id"] for j in self.j}
        self._id_to_name = {j["id"]: j["name_fi"] for j in self.j}

    def __iter__(self):
        for j in self.j:
            c = self[j["id"]]
            yield c

    def __getitem__(self, key: int):
        return self._get_by_name_or_id(key, Constituency.create)

    def name_to_id(self, name: str):
        return self._name_to_id.get(name, None)

    def id_to_name(self, key: int):
        return self._id_to_name.get(key, None)


class Constituency:
    def __init__(self, container: Constituencies, key: int, j: dict):
        self.api = container.api
        self.container = container
        self.id = key
        self.j = j
        self.parties = Parties(self)
        self.candidates = Candidates(self)
        self.questions = Questions(self)

    def __repr__(self):
        return f"Constituency({self.id}, {self.name})"

    @property
    def name(self):
        return self.j["name_fi"]

    def stats_by_party(self):
        stats = StatsByParty()
        for candidate in self.candidates:
            for answer in candidate.answers:
                if answer.question.type == "ONE_TO_FIVE":
                    stats.add(answer.question, candidate.party, answer.normalized_value)
        return stats

    @staticmethod
    def create(constituencies, key):
        for j in constituencies.j:
            if j["id"] == key:
                return Constituency(constituencies, key, j)
        return None


class Parties(_Container):
    def __init__(self, constituency: Constituency):
        super().__init__(constituency.api)
        self.constituency = constituency
        self.j = constituency.api.parties(constituency.id)
        self._name_to_id = {j["short_name_fi"]: j["id"] for j in self.j}
        self._id_to_name = {j["id"]: j["short_name_fi"] for j in self.j}

    def __iter__(self):
        for j in self.j:
            p = self[j["id"]]
            yield p

    def __getitem__(self, key):
        return self._get_by_name_or_id(key, Party.create)

    def name_to_id(self, name: str):
        return self._name_to_id.get(name, None)

    def id_to_name(self, key: int):
        return self._id_to_name.get(key, None)


class Candidates(_Container):
    def __init__(self, constituency):
        super().__init__(constituency.api)
        self.api = constituency.api
        self.constituency = constituency
        self.j = self.api.candidates(constituency.id)

    def __iter__(self):
        for j in self.j:
            c = self[j["id"]]
            yield c

    def __getitem__(self, key):
        return self._get_by_id(key, Candidate.create)

    def find(self, name):
        return [c for c in self if c.full_name == name]


class Questions(_Container):
    def __init__(self, constituency):
        super().__init__(constituency.api)
        self.constituency = constituency
        self.j = constituency.api.questions(constituency.id)

    def __iter__(self):
        for j_category in self.j:
            for j_question in j_category["questions"]:
                q = self[j_question["id"]]
                yield q

    def __getitem__(self, key):
        return self._get_by_id(key, Question.create)


class Party:
    def __init__(self, parties: Parties, key: int, j: dict):
        self.parties = parties
        self.id = key
        self.j = j

    def __repr__(self):
        return f"Party({self.id}, {self.name} ({self.abbreviation}))"

    @property
    def name(self):
        return self.j["name_fi"]

    @property
    def abbreviation(self):
        return self.j["short_name_fi"]

    @staticmethod
    def create(parties, key):
        for j in parties.j:
            if j["id"] == key:
                return Party(parties, key, j)
        return None


class Question:
    def __init__(self, parent: Questions, key: int, j: dict):
        self.parent = parent
        self.id = key
        self.j = j

    def __repr__(self):
        return f'Question({self.id}, "{self.text[:48]}...")'

    @property
    def text(self):
        return self.j["text_fi"]

    @property
    def type(self):
        return self.j["type"]

    @staticmethod
    def create(questions, key):
        for j in questions.j:
            for j2 in j["questions"]:
                if j2["id"] == key:
                    return Question(questions, key, j2)
        raise RuntimeError()


class Candidate:
    def __init__(self, container: Candidates, key: int, j: dict):
        self.api = container.api
        self.container = container
        self.id = key
        self.j = j
        self.answers = Answers(self)
        self.party = self.container.constituency.parties[self.j["party_id"]]

    def __repr__(self):
        return f'Candidate({self.id}, "{self.full_name}")'

    @property
    def constituency(self):
        return self.container.constituency

    @property
    def first_name(self):
        return self.j["first_name"]

    @property
    def last_name(self):
        return self.j["last_name"]

    @property
    def language(self):
        return self.j["info"]["language"][f"name_fi"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def create(candidates, key):
        j = candidates.api.candidate(candidates.constituency.id, key)
        if j:
            return Candidate(candidates, key, j)
        return None


class Answers:
    def __init__(self, candidate: Candidate):
        self.candidate = candidate
        self.j = candidate.j["answers"]
        self._id_to_answer = {}

    def __iter__(self):
        for key in self.j:
            a = self[int(key)]
            yield a

    def __getitem__(self, key: int):
        if key not in self._id_to_answer:
            if str(key) not in self.j:
                return None
            self._id_to_answer[key] = Answer(self, key)
        return self._id_to_answer[key]


class Answer:
    def __init__(self, container: Answers, key: int):
        self.container = container
        self.question = container.candidate.container.constituency.questions[key]
        self.j = container.j[str(key)]

    def __repr__(self):
        return (
            f"Answer({self.container.candidate.id}, {self.question.id}, {self.value})"
        )

    @property
    def value(self):
        return self.j["answer"]

    @property
    def normalized_value(self):
        return self.value - 3
