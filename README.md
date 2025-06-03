# ProfileTranferUtil

**ProfileTransferUtil** is a CLI utility for securely copying a user's Windows profile from a remote machine to a local destination. It uses `robocopy` under the hood and supports selectively syncing `AppData` folders, excluding temporary files, and performing safe dry runs. Ideal for IT professionals handling user migrations or profile backups.

---

## Features

* ✅ Sync entire user profile directories from remote Windows machines.
* 🔐 Supports UNC path authentication prompts.
* 📁 Configurable includes and excludes via `config.toml`.
* 💨 Dry-run mode for safe simulations before committing file copies.
* 🧹 Post-processing support like removing Mark of the Web (MotW) from `.lnk` files.

---

## Installation

### Requirements

* Python 3.8+
* Windows OS with `robocopy` available (built-in on modern versions)
* PyInstaller (optional, for packaging)
* Optional dependencies:

  * [`toml`](https://pypi.org/project/toml/) (install via `pip install toml`)

### Clone

```bash
git clone https://github.com/yourusername/profilesync.git
cd profilesync
```

---

## Configuration

All settings are managed via a `config.toml` file, which defines:

* Profile path structure
* Robocopy arguments
* Include/exclude folder rules

If `config.toml` is not found in the working directory, the default version bundled with the executable will be extracted.

---

## Usage

### From Source

```bash
python main.py [--machine REMOTE_HOST] [--username USER] [--destination DEST_PATH] [--dryrun]
```

If any parameters are omitted, they will be prompted interactively.

#### Example

```bash
python main.py --machine WS-07 --username jsmith --destination D:\Backups\jsmith
```

---

## Dry Run

Use the `--dryrun` flag to simulate the copy process without making changes:

```bash
python main.py --dryrun
```

---

## Building a Standalone Executable

To bundle the tool into a single `.exe` for distribution:

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Create the Executable

```bash
pyinstaller main.py --onefile --add-data "config.toml;." --name ProfileSync
```

* `--onefile`: bundles everything into one `.exe`
* `--add-data`: embeds `config.toml` for use at runtime
* `--name`: sets the output filename

> ⚠️ On Windows, use `;` instead of `:` for `--add-data` paths.

### Output

The final executable will be located at:

```
dist\ProfileSync.exe
```

---

## Logging & Behavior

* Logs are printed to console in a human-friendly format.
* If UNC access fails, authentication is prompted using a built-in helper.
* The program performs post-processing by removing Mark of the Web from `.lnk` files in the user's Desktop folder.

---

## Development & Testing

Run unit tests with:

```bash
pytest
```

Tests mock all major operations and validate dry-run behavior, config loading, and robocopy command generation.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a new feature branch
3. Submit a pull request with clear context and test coverage

---

## License

MIT License. See [LICENSE](LICENSE) for full details.

---

## Credits

* Thanks to open source tools: `robocopy`, `toml`, `PyInstaller`

