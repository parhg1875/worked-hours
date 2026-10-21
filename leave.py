import json
import os
import pandas as pd


class Leave_manager:
    '''
    Saving and summing employees' leaves (annual, sick, hourly)
    '''
    DAY_HOURS = 8   # each leave day = 8 hours
    TYPES = {
        "استحقاقی": "days",
        "استعلاجی": "days",
        "ساعتی": "hours",
    }

    def __init__(self, path="leaves.json"):
        # store next to this file, so the path doesn't depend on the working directory
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        self.path = path
        self.records = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def add(self, emp_id, date, leave_type, amount):
        year, month, _ = [int(x) for x in date.split("/")]

        if self.TYPES[leave_type] == "days":
            hours = amount * self.DAY_HOURS
        else:
            hours = amount

        self.records.append({
            "id": int(emp_id),
            "date": date,
            "سال": year,
            "ماه_شمسی": month,
            "type": leave_type,
            "amount": amount,
            "leave_hours": float(hours),
        })
        self._save()

    def to_dataframe(self):
        cols = ["id", "سال", "ماه_شمسی", "leave_hours"]
        if not self.records:
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(self.records)
        df["id"] = df["id"].astype(int)
        df["سال"] = df["سال"].astype(int)
        df["ماه_شمسی"] = df["ماه_شمسی"].astype(int)
        return df.groupby(["id", "سال", "ماه_شمسی"], as_index=False)["leave_hours"].sum()