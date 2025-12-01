import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import app.models
print(f"Has GeneratedReport: {'GeneratedReport' in dir(app.models)}")
print(f"Has Report: {'Report' in dir(app.models)}")
if 'GeneratedReport' in dir(app.models):
    print(f"GeneratedReport: {app.models.GeneratedReport}")
    print(f"GeneratedReport module: {app.models.GeneratedReport.__module__}")
