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
            try:
                item = create(self, key)
                self._id_to_item[key] = item
            except ConnectionError:
                return None
        return self._id_to_item[key]


class Constituencies(_Container):
    def __init__(self, api=None):
        api = api or PublicApi()
        super().__init__(api)
        self.j = self.api.constituencies()
        self._name_to_id = {j["name_fi"]: j["id"] for j in self.j}
        self._id_to_name = {j["id"]: j["name_fi"] for j in self.j}

    def __iter__(self):
        for j in self.j:
            c = self[j["id"]]
            if c:
                yield c

    def __getitem__(self, key: int):
        return self._get_by_name_or_id(key, Constituency)

    def name_to_id(self, name: str):
        return self._name_to_id.get(name, None)

    def id_to_name(self, key: int):
        return self._id_to_name.get(key, None)


class Constituency:
    def __init__(self, container: Constituencies, key: int):
        self.api = container.api
        self.container = container
        self.id = key
        self.j = Constituency._find(self.container.j, self.id)
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
    def _find(j, key):
        for i in j:
            if i["id"] == key:
                return i
        raise RuntimeError()


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
            if p:
                yield p

    def __getitem__(self, key):
        return self._get_by_name_or_id(key, Party)

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
            if c:
                yield c

    def __getitem__(self, key):
        return self._get_by_id(key, Candidate)

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
                if q:
                    yield q

    def __getitem__(self, key):
        return self._get_by_id(key, Question)


class Party:
    def __init__(self, parent, key):
        self.parent = parent
        self.id = key
        self.j = Party._find(self.parent.j, self.id)

    def __repr__(self):
        return f"Party({self.id}, {self.name} ({self.abbreviation}))"

    @property
    def name(self):
        return self.j["name_fi"]

    @property
    def abbreviation(self):
        return self.j["short_name_fi"]

    @staticmethod
    def _find(j, key):
        return next(i for i in j if i["id"] == key)


class Question:
    def __init__(self, parent, key):
        self.parent = parent
        self.id = key
        self.j = Question._find(self.parent.j, self.id)

    def __repr__(self):
        return f'Question({self.id}, "{self.text[:48]}...")'

    @property
    def text(self):
        return self.j["text_fi"]

    @property
    def type(self):
        return self.j["type"]

    @staticmethod
    def _find(j, key):
        for j_category in j:
            for j_question in j_category["questions"]:
                if j_question["id"] == key:
                    return j_question
        raise RuntimeError()


class Candidate:
    def __init__(self, container, key):
        self.api = container.api
        self.container = container
        self.id = key
        self.j = self.api.candidate(container.constituency.id, self.id)
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
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Answers:
    def __init__(self, candidate: Candidate):
        self.candidate = candidate
        self.j = candidate.j["answers"]
        self._id_to_answer = {}

    def __iter__(self):
        for key in self.j:
            a = self[int(key)]
            if a:
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
