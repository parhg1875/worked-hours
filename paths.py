import os
import sys


def app_dir():
    """
    Folder where the program lives:
    - when running as an exe: the folder that contains the exe
    - when running as a script: the folder that contains the .py files
    Files that must survive between runs (leaves.json) are stored here.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))