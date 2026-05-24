# logger.py
import logging, os, sys
from datetime import datetime

_DIR     = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

_LOG_FILE = os.path.join(_LOG_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
_fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
_fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_ch = logging.StreamHandler(sys.stdout)
_fh.setFormatter(_fmt); _ch.setFormatter(_fmt)

log = logging.getLogger("bot")
if not log.handlers:
    log.setLevel(logging.DEBUG)
    log.addHandler(_fh)
    log.addHandler(_ch)
