import requests
import pandas as pd
from collections import Counter
import time

url = 'https://pnldev.com/api/calender?year=1404&holiday=false'

res = requests.get(url)

class  Calendar:
    def __init__(self, years):
        self.years = years
        self.months = [
        "فروردین", "اردیبهشت", "خرداد",
        "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر",
        "دی", "بهمن", "اسفند"
    ]
        self.weekdays = {
        "ش": "شنبه",
        "ی": "یکشنبه",
        "د": "دوشنبه",
        "س": "سه‌شنبه",
        "چ": "چهارشنبه",
        "پ": "پنجشنبه",
        "ج": "جمعه"
    }
    def calender_date(self, month):
        rows = []

        for year in self.years:

                month_number = month

                print(f"در حال دریافت {year}/{month_number} ...")

                url = f"https://pnldev.com/api/calender?year={year}&month={month_number}"

                try:
                    res = requests.get(url, timeout=10)
                    data = res.json()

                    if data["status"] == False:
                        print("خطا:", data["result"])
                        continue

                    days = data["result"]

                    counter = Counter()
                    holidays = []
                    wednesday = []
                    for info in days.values():

                        day_week = info["solar"]["dayWeek"]
                        counter[day_week] += 1

                        if info["holiday"] and day_week != "ج" and day_week != "پ":
                            day = info["solar"]["day"]
                            weekday = self.weekdays[day_week]

                            holidays.append(f"{day} {weekday}")
                        if info["holiday"] and day_week == "پ":
                            day = info["solar"]["day"]
                            weekday = self.weekdays[day_week]

                            wednesday.append(f"{day} {weekday}")

                    row = {
                        "سال": year,
                        "ماه": self.months[month_number - 1],
                        "ماه_شمسی": month_number,
                        "تعداد روز": len(days),

                        "شنبه": counter["ش"],
                        "یکشنبه": counter["ی"],
                        "دوشنبه": counter["د"],
                        "سه‌شنبه": counter["س"],
                        "چهارشنبه": counter["چ"],
                        "پنجشنبه": counter["پ"],
                        "جمعه": counter["ج"],

                        "تعداد تعطیلات": len(holidays),
                        "روزهای تعطیل": holidays,
                        "تعداد پنجشنبه های تعطیل": len(wednesday),
                        "پنجشنبه های تعطیل": wednesday
                    }

                    rows.append(row)

                    time.sleep(0.5)

                except requests.exceptions.Timeout:
                    print(f" {year}/{month_number} زمان درخواست تمام شد")

                except requests.exceptions.RequestException as e:
                    print(f" خطا در {year}/{month_number}: {e}")
    
        df_cale = pd.DataFrame(rows)
        
        df_cale = df_cale.sort_values(
            by=["سال", "ماه_شمسی"]
        ).reset_index(drop=True)

        return df_cale
