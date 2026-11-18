# File Organizer

A Python command-line tool that sorts the files in a folder into subfolders by extension. It uses only the standard library and runs on Python 3.9 or newer.

## Usage

From the repository directory, preview the moves first:

```sh
python3 organizer.py ~/Downloads --dry-run
```

```text
boarding-pass.pdf -> Documents/boarding-pass.pdf
holiday.JPG -> Images/holiday.JPG
sample.zip -> Archives/sample.zip
```

Run the same command without `--dry-run` to move the files:

```sh
python3 organizer.py ~/Downloads
```

The tool creates `Images`, `Documents`, `Audio`, `Videos`, `Archives`, and `Others` as needed. Files with unfamiliar or missing extensions go into `Others`. It processes only the files directly inside the chosen folder and skips dotfiles and symlinks.

If `Documents/report.pdf` already exists, an incoming `report.pdf` becomes `Documents/report_1.pdf`. The suffix increases until a name is available. If a move fails, the tool reports the error and stops. You can fix the issue and run the command again to process the remaining files.

## Tests

```sh
python3 -m unittest discover -s tests
```
