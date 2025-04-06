import pathlib
import json

import requests


def _str(l: list | tuple) -> list:
    return [str(e) for e in l]


class PublicApi:
    CACHE_ROOT = ".ylekone-cache"
    YLE_URL_PREFIX = "https://vaalit.yle.fi/vaalikone"

    @staticmethod
    def _avkv25_prefix():
        return f"{PublicApi.YLE_URL_PREFIX}/alue-ja-kuntavaalit2025/api/public"

    @staticmethod
    def kv25():
        return PublicApi(f"{PublicApi._avkv25_prefix()}/municipality")

    @staticmethod
    def av25():
        return PublicApi(f"{PublicApi._avkv25_prefix()}/county")

    def __init__(self, base_url: str):
        self.base_url = base_url
        pathlib.Path(self.cache_dir).mkdir(exist_ok=True, parents=True)

    @property
    def cache_dir(self) -> str:
        return f"{PublicApi.CACHE_ROOT}/{self.election}/{self.kind}"

    @property
    def election(self) -> str:
        return self.base_url.split("/vaalikone/")[1].split("/")[0]

    @property
    def kind(self) -> str:
        return self.base_url.split("/api/public/")[1].split("/")[0]

    @property
    def tail(self) -> str:
        return self.base_url.split("/vaalikone/")[1].split("/")[0]

    def url(self, *args) -> str:
        return "/".join([self.base_url] + _str(args))

    def cache_path(self, *args) -> str:
        return f"{self.cache_dir}/{'-'.join(_str(args))}.json"

    def fetch(self, *args):
        """Fetch without caching"""
        url = self.url(*args)
        headers = dict(Accept="application/json")
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(url)
            return None
        try:
            j = response.json()
            return j
        except json.JSONDecodeError:
            print(url)
            return None

    def fetch_cached(self, *args):
        cache_path = self.cache_path(*args)
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            j = self.fetch(*args)
            if j is not None:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(j, f, indent=4)
            return j

    def constituencies(self):
        return self.fetch_cached("constituencies")

    def parties(self, constituency_id):
        return self.fetch_cached("constituencies", constituency_id, "parties")

    def candidate(self, constituency_id, candidate_id):
        return self.fetch_cached(
            "constituencies", constituency_id, "candidates", candidate_id
        )

    def candidates(self, constituency_id):
        return self.fetch_cached("constituencies", constituency_id, "candidates")

    def questions(self, constituency_id):
        return self.fetch_cached("constituencies", constituency_id, "questions")
