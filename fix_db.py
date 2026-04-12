import sys
import os

sys.path.insert(0, os.path.abspath('.'))
from app.db import execute

execute("UPDATE llm_config SET selected_model='gemma4:e4b', fallback_model='gemma4:e4b'")
print("Database updated!")
