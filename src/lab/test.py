import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from tools.estate_web_crowling import export_policy_factors

saved_path = export_policy_factors(max_page=3)
print(saved_path)
