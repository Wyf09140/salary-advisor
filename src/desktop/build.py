"""Build the desktop notch app into dist/SalaryAdvisor/SalaryAdvisor.exe. Owner: Sophak.

Run:  python -m src.desktop.build        (needs: pip install -r requirements-desktop.txt)

One-folder build (starts fast; zip dist/SalaryAdvisor to share). Bundles the page and config files at the
same relative paths src/config.py expects, so ROOT-based paths keep working inside the bundle.
NOTE: once predict() loads real models (models/*.pkl, SBERT), add them to DATAS and expect a much larger
bundle if PyTorch comes along; see the README "Desktop app" section.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEP = os.pathsep  # PyInstaller --add-data uses ';' on Windows
DATAS = [
    (ROOT / "web" / "index.html", "web"),
    (ROOT / "config", "config"),
]
HIDDEN = ["pypdf", "docx"]  # imported lazily inside resume_parser.extract_text
EXCLUDE = ["torch", "sentence_transformers", "xgboost", "sklearn", "statsmodels", "pandas", "matplotlib",
           "streamlit", "kaggle", "pyarrow", "tkinter"]  # not used by the desktop app today


def main() -> None:
    import PyInstaller.__main__

    args = [
        str(ROOT / "src" / "desktop" / "__main__.py"),
        "--name", "SalaryAdvisor", "--windowed", "--noconfirm", "--clean",
        "--paths", str(ROOT),
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"), "--specpath", str(ROOT / "build"),
    ]
    for src, dest in DATAS:
        args += ["--add-data", f"{src}{SEP}{dest}"]
    for mod in HIDDEN:
        args += ["--hidden-import", mod]
    for mod in EXCLUDE:
        args += ["--exclude-module", mod]
    PyInstaller.__main__.run(args)
    print(f"\nBuilt: {ROOT / 'dist' / 'SalaryAdvisor' / 'SalaryAdvisor.exe'}")


if __name__ == "__main__":
    sys.exit(main())
