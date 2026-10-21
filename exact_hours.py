class Exact_hour:
    '''
    Calculating hours that the employees must spend to work
    '''
    def __init__(self, df_cale, total_worked, leaves=None):
        self.df_cale = df_cale
        self.total_worked = total_worked
        self.leaves = leaves
        self.result = None

    def calculate(self):
        # calculate the exact hours with dropping off days
        self.df_cale["certain_h"] = (
            (self.df_cale["تعداد روز"]
             - self.df_cale["پنجشنبه"]
             - self.df_cale["جمعه"]
             - self.df_cale["تعداد تعطیلات"]) * 8
        ) + (
            (self.df_cale["پنجشنبه"]
             - self.df_cale["تعداد پنجشنبه های تعطیل"]) * 5
        )

        calendar_hours = self.df_cale[
            ["سال", "ماه_شمسی", "certain_h"]
        ]

        self.result = self.total_worked.merge(
            calendar_hours,
            on=["سال", "ماه_شمسی"]
        )

        # leaves (annual, sick, hourly)
        if self.leaves is not None and not self.leaves.empty:
            self.result = self.result.merge(
                self.leaves,
                on=["id", "سال", "ماه_شمسی"],
                how="left"
            )
            self.result["leave_hours"] = self.result["leave_hours"].fillna(0)
        else:
            self.result["leave_hours"] = 0.0

        # subtract leave hours from the required hours
        self.result["certain_h"] = (
            self.result["certain_h"] - self.result["leave_hours"]
        ).clip(lower=0)

        self.result["difference"] = (
            self.result["certain_h"]
            - self.result["worked_hours"])
        self.result["overtime"] = (
            self.result["difference"].where(self.result["difference"] < 0, 0) * -1)
        self.result["shortage"] = (
            self.result["difference"].where(self.result["difference"] > 0, 0))
        return self.result