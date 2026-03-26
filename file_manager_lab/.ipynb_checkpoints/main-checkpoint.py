from config import WORKSPACE_ROOT
from file_manager.cli import CommandLineInterface


def main() -> None:
    cli = CommandLineInterface(WORKSPACE_ROOT)
    cli.run()


if __name__ == '__main__':
    main()
