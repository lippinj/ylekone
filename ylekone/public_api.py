import pathlib
import json

import requests


class PublicApi:
    CACHE_DIR = ".ylekone-cache"
    YLE_URL_PREFIX = "https://vaalit.yle.fi/vaalikone"

    def __init__(self, election="alue-ja-kuntavaalit2025", folder="municipality"):
        self.election = election
        self.folder = folder
        self.prefix = f"{PublicApi.YLE_URL_PREFIX}/{election}/api/public/{folder}"
        pathlib.Path(PublicApi.CACHE_DIR).mkdir(exist_ok=True)

    def fetch(self, s):
        """Fetch without caching"""
        url = f"{self.prefix}/{s}"
        headers = dict(Accept="application/json")
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            return None
        try:
            j = response.json()
            return j
        except json.JSONDecodeError:
            return None

    def fetch_cached(self, s):
        cache_basename = f"{self.folder}/{s}".replace("/", "-")
        cache_path = f"{PublicApi.CACHE_DIR}/{cache_basename}.json"
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            j = self.fetch(s)
            if j is not None:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(j, f, indent=4)
            return j

    def constituencies(self):
        return self.fetch_cached("constituencies")

    def parties(self, constituency_id):
        return self.fetch_cached(f"constituencies/{constituency_id}/parties")

    def candidate(self, constituency_id, candidate_id):
        return self.fetch_cached(
            f"constituencies/{constituency_id}/candidates/{candidate_id}"
        )

    def candidates(self, constituency_id):
        return self.fetch_cached(f"constituencies/{constituency_id}/candidates")

    def questions(self, constituency_id):
        return self.fetch_cached(f"constituencies/{constituency_id}/questions")
