from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).resolve().parent
requirements = []

requirements_path = BASE_DIR / "requirements.txt"
if requirements_path.exists():
    requirements = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

setup(
    name="LLMOPS-3",
    version="0.1.0",
    author="Kshitij",
    description="Study Buddy project",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)