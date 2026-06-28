import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

root = Path(os.getenv("CSCMS_ROOT", "")).expanduser()

required_folders = [
    "Photos to Review",
    "AI Selected Photos",
    "Ready for Approval",
    "Brand Assets",
    "Logs",
]

print(f"CSCMS_ROOT: {root}")

if not root.exists():
    raise FileNotFoundError(f"Root folder does not exist: {root}")

for folder in required_folders:
    path = root / folder
    if path.exists():
        print(f"OK: {path}")
    else:
        print(f"MISSING: {path}")

lower_third = root / "Brand Assets" / "RPI-CSCMS-Automate-Lower-Third.png"

if lower_third.exists():
    print(f"OK lower third: {lower_third}")
else:
    print(f"MISSING lower third: {lower_third}")

print("Setup check complete.")