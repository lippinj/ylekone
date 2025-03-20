import numpy as np


class GroupStats:
    """Aggregate statistics of a group of respondents"""

    def __init__(self, options=(-2, -1, +1, +2)):
        self.options = options
        self.array = [0, 0, 0, 0]
        self.total = 0

    def add(self, x):
        """Add a response"""
        self.array[self.options.index(x)] += 1
        self.total += 1

    def __getitem__(self, x):
        return self.array[self.options.index(x)]

    def __repr__(self):
        return f"<GroupStats([{','.join(self.array)}])>"

    @property
    def mean(self):
        """Mean answer: E[x]"""
        return np.dot(self.array, self.options) / self.total if self.total else 0

    @property
    def mean_square(self):
        """Mean square answer: E[x²]"""
        options_square = np.pow(self.options, 2)
        return np.dot(self.array, options_square) / self.total if self.total else 0

    @property
    def var(self):
        """Answer variance: Var(x) = E[x²] - E[x]²"""
        return self.mean_square - self.mean**2

    @property
    def std(self):
        """Answer standard deviation: Std(x) = √(Var[x])"""
        return np.sqrt(self.var)

    @property
    def pretty_numbers(self):
        return f"{self.pretty_votes} | {self.pretty_statistics}"

    @property
    def pretty_votes(self):
        SYMBOLS = ("⮇", "⭣", "⭡", "⮅")
        return " ".join(f"{s}:{n:<3}" for s, n in zip(SYMBOLS, self.array))

    @property
    def pretty_statistics(self):
        return f"μ:{self.mean:<+5.2f} σ:{self.std:<+5.2f}"
