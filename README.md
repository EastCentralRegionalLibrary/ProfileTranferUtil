# ProfileTranferUtil

**ProfileTransferUtil** is a CLI utility for copying a user's Windows profile from a remote ( or local with 127.0.0.1 ) machine to a local destination. It uses `robocopy` and `psexec` under the hood and supports selectively syncing *local* registry keys, `AppData` folders, excluding temporary files, and performing safe dry runs. Ideal for IT professionals handling user migrations or profile backups.

---
## Disclaimer

⚠️ **Warning:** This tool is under active development and may not be suitable for production use. While it is functional for internal testing and migration tasks it has not been fully validated for production environments. Use with caution! Perform dry runs and validate all outputs before committing changes. 

This software is provided "as is" without any warranties, express or implied.  
By using this tool, you acknowledge and agree that:

* The author(s) and contributors shall not be held liable for any data loss, corruption, damage, or other issues arising from the use, misuse, or inability to use this software.
* You assume full responsibility for verifying outputs and ensuring backups before performing any operations.
* Use at your own risk!

---

## Features

* ✅ Sync entire user profile directories from remote Windows machines.
* 🔐 Supports UNC path authentication prompts.
* 📁 Configurable includes and excludes via `config.toml`.
* 💨 Dry-run mode for safe simulations before committing file copies.
* 🧹 Post-processing support like removing Mark of the Web (MotW) from `.lnk` files.
* ⚙️ Registry Export with PsExec: Export specified local registry keys to .reg files, optionally using PsExec to run as the logged-in user (session 1) for appropriate permissions.
* 🔍 PsExec Verification: Automatically checks for PsExec.exe in PATH or a specified custom location before execution.
---

## Installation

### Requirements

* Python 3.8+
* Windows OS with `robocopy` available (built-in on modern versions)
* PyInstaller (optional, for packaging)
* PsExec.exe (optional, for registry export functionality - available from Sysinternals Suite)
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
* Include registry paths

If `config.toml` is not found in the working directory, the default version bundled with the executable will be extracted.

---

## Usage

### From Source

```bash
python main.py [--machine REMOTE_HOST] [--username USER] [--destination DEST_PATH] [--psexec] [--dryrun]
```

If any required parameters are omitted, they will be prompted interactively.

#### Example

```bash
python main.py --machine WS-07 --username jsmith --destination D:\Backups\jsmith
```

---

## Dry Run

Use the `--dryrun` flag to simulate the copy process without making changes:

## PsExec

Use the `--psexec` flag to disable the use of PsExec for registry exports.

Note on PsExec:

    Ensure PsExec.exe is either in your system's PATH environment variable, in the same directory as the script, or provide its full path via the psexec_custom_path argument if calling reg_export directly.

    Using PsExec which is enabled by default will attempt to run the reg export command interactively in session 1 with elevated privileges.

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

