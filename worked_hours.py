import pandas as pd
# print(res.json())
class Worked_hour:
    '''
    Calculating hours that the employees spent to work
    '''
    def __init__(self, file):
        self.file = file
        self.df = None
        self.read_csv()
    def read_csv(self):
        #read file(csv)
        self.df = pd.read_csv(self.file, header=None)
        self.df.columns = ["id", "ent/exi", "date", "fingerprint", "a", "b"]
    def calculate(self):
        #change the fomat of column to H:M:S
        self.df["ent/exi"] = pd.to_datetime(self.df["ent/exi"], format = "%H:%M:%S")

        # define date: year, month
        self.df["date"] = self.df["date"].astype(str)
        self.df["سال"] = self.df["date"].str.split("/").str[0].astype(int)
        self.df["ماه_شمسی"] = self.df["date"].str.split("/").str[1].astype(int)

        # sorting values in order id, ent/exi, date 
        self.df.sort_values(["id","ent/exi","date"], inplace=True)

        # calculate the next time of work at the same time
        self.df["next_time"] = self.df.groupby(["id", "date"])["ent/exi"].shift(-1)

        # calculate hours that the employees spent to work
        self.df["worked"] = self.df["next_time"] - self.df["ent/exi"]

        # changing its type to seconds
        self.df["worked_hours"] = (self.df["worked"].dt.total_seconds()) / 3600

        # handling missing values
        self.df["worked_hours"].fillna(0, inplace=True)
        
        # calculate hours that the employees spent to work in order ماه_شمسی, سال, id
        self.total_worked = self.df.groupby(["id", "سال", "ماه_شمسی"], as_index=False)["worked_hours"].sum()
        return self.total_worked



