import os
import shutil
import sys
from pathlib import Path
import tomllib  # Python 3.11+


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running inside PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_config(config_path: str = "config.toml") -> dict:
    """
    Load the config.toml file. If not found, extract a default one from the bundled resources.
    """
    config_file = Path(config_path)

    if not config_file.exists():
        # Fallback to bundled config and copy it out
        default_config_path = resource_path("config.toml")
        shutil.copy(default_config_path, config_path)
        print(f"[INFO] Default config.toml copied to {config_path}")

    with open(config_file, "rb") as f:
        return tomllib.load(f)
