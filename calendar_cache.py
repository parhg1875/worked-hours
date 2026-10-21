import json
import os

import pandas as pd

from paths import app_dir


class Calendar_cache:
    '''
    Saves each (year, month) calendar row locally, so the API
    is called only once per month (the next runs work offline).
    '''

    def __init__(self, path="calendar_cache.json"):
        if not os.path.isabs(path):
            path = os.path.join(app_dir(), path)
        self.path = path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(
                    self.data, f, ensure_ascii=False, indent=2,
                    default=lambda o: o.item() if hasattr(o, "item") else str(o)
                )
        except OSError:
            # cache is only an optimization; ignore write errors
            pass

    @staticmethod
    def _key(year, month):
        return f"{int(year)}/{int(month)}"

    def get(self, year, month):
        records = self.data.get(self._key(year, month))
        if not records:
            return None
        return pd.DataFrame(records)

    def put(self, year, month, df):
        self.data[self._key(year, month)] = df.to_dict("records")
        self._save()