from api import Calendar
from exact_hours import Exact_hour
from worked_hours import Worked_hour
import tkinter as tk
from gui import WorkedHoursGUI

calender = Calendar([1404, 1405])
df_cale = calender.calender_date(10)
worked = Worked_hour("C:\\Users\\parni\\OneDrive\\Desktop\\python exercises\\project\\fingerprints.TXT")
total_worked = worked.calculate()
exact = Exact_hour(df_cale, total_worked)
result = exact.calculate()
print(result)
def main(): 
    root = tk.Tk() 
    app = WorkedHoursGUI(root) 
    root.mainloop() 
if __name__ == "__main__": 
    main()