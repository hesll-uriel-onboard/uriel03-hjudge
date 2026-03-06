import os
import pathlib
import sys
from argparse import ArgumentParser

VERSION_NUMBER_LENGTH = 4


def change_cwd_and_get_all_files() -> list[str]:
    THIS_DIRECTORY = pathlib.Path(__file__).parent
    os.chdir(THIS_DIRECTORY.parent)
    VERSION_DIRECTORY = str(pathlib.Path(__file__).parent) + "/versions"
    return os.listdir(VERSION_DIRECTORY)


def get_current_version(files: list[str]) -> int:
    max_version = 0
    for filename in files:
        try:
            number = int(filename.split("_")[0])
            max_version = max(max_version, number)
        except Exception:
            pass
    return max_version


def create_parser(default_version: int) -> ArgumentParser:
    parser = ArgumentParser(
        prog="new-version", description="make new alembic file"
    )
    parser.add_argument("-m", "--msg", required=True)
    parser.add_argument("-v", "--ver", default=default_version, type=int)
    return parser


def main():
    files = change_cwd_and_get_all_files()
    current_version = get_current_version(files)
    next_version = current_version + 1
    parser = create_parser(next_version)

    result = parser.parse_args(sys.argv[1:])
    if result.ver < next_version:
        parser.error(f"next version must be greater than {current_version}")
    next_version = result.ver

    COMMAND = f'uv run alembic revision --rev-id {str(next_version).zfill(VERSION_NUMBER_LENGTH)} --message "{result.msg}"'
    os.system(COMMAND)


if __name__ == "__main__":
    main()
