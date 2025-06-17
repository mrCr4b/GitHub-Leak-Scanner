# common_helpers.py  (make a tiny new module)
from pathlib import Path
import sys, os

def base_dir() -> Path:
    """
    Return the directory where *your code* lives:
      • project folder when running from source
      • _MEIPASS temp folder when running from PyInstaller EXE
    """
    if getattr(sys, 'frozen', False):          # PyInstaller sets this
        return Path(sys._MEIPASS)              # type: ignore
    return Path(__file__).resolve().parent
