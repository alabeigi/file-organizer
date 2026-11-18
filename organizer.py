import argparse
import os
from pathlib import Path


EXTENSIONS = {
    "Images": {
        ".avif", ".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp",
    },
    "Documents": {
        ".csv", ".doc", ".docx", ".md", ".odt", ".pdf", ".ppt", ".pptx", ".rtf", ".txt", ".xls", ".xlsx",
    },
    "Audio": {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"},
    "Videos": {".avi", ".mkv", ".mov", ".mp4", ".webm"},
    "Archives": {".7z", ".bz2", ".gz", ".rar", ".tar", ".xz", ".zip"},
}
CATEGORY_BY_SUFFIX = {
    suffix: category for category, suffixes in EXTENSIONS.items() for suffix in suffixes
}


def check_category(directory):
    if directory.is_symlink() or (os.path.lexists(directory) and not directory.is_dir()):
        raise OSError(f"Cannot use {directory} as a category folder")


def available_destination(source, directory, reserved_names):
    destination = directory / source.name
    number = 1
    while destination.name.casefold() in reserved_names or os.path.lexists(destination):
        destination = directory / f"{source.stem}_{number}{source.suffix}"
        number += 1
    return destination


def plan_moves(folder):
    moves = []
    reserved_by_category = {}
    for source in sorted(folder.iterdir(), key=lambda entry: entry.name):
        if source.name.startswith(".") or source.is_symlink() or not source.is_file():
            continue

        category = CATEGORY_BY_SUFFIX.get(source.suffix.lower(), "Others")
        directory = folder / category
        if category not in reserved_by_category:
            check_category(directory)
            reserved_by_category[category] = set()

        reserved_names = reserved_by_category[category]
        destination = available_destination(source, directory, reserved_names)
        reserved_names.add(destination.name.casefold())
        moves.append((source, destination))
    return moves


def move_file(source, destination):
    directory = destination.parent
    directory.mkdir(exist_ok=True)
    check_category(directory)

    # Reserve the name exclusively before replacing it with the source file.
    with destination.open("xb"):
        pass
    try:
        source.replace(destination)
    except OSError:
        destination.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sort files in a folder by extension.")
    parser.add_argument("folder", type=Path, help="folder containing the files to sort")
    parser.add_argument("--dry-run", action="store_true", help="show moves without making changes")
    args = parser.parse_args(argv)

    try:
        folder = args.folder.expanduser()
        moves = plan_moves(folder)
        if not moves:
            print("No files to organize.")
            return 0

        for source, destination in moves:
            if not args.dry_run:
                move_file(source, destination)
            relative_path = destination.relative_to(folder).as_posix()
            print(f"{source.name} -> {relative_path}")
    except (OSError, RuntimeError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
