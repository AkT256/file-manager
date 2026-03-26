from __future__ import annotations

import shlex
from pathlib import Path

from .core import FileManager
from .exceptions import FileManagerError, InvalidCommandError


class CommandLineInterface:
    def __init__(self, workspace_root: Path):
        self.manager = FileManager(workspace_root)

    def execute(self, command_line: str) -> str:
        parts = shlex.split(command_line)
        if not parts:
            return ''

        command = parts[0].lower()
        args = parts[1:]

        match command:
            case 'help':
                return self.manager.help()
            case 'pwd':
                return self.manager.pwd()
            case 'ls':
                items = self.manager.ls()
                return '\n'.join(items) if items else 'Папка пуста.'
            case 'tree':
                lines = self.manager.tree()
                return '\n'.join(lines) if lines else 'Папка пуста.'
            case 'cd':
                self._expect_args(args, 1)
                return self.manager.cd(args[0])
            case 'mkdir':
                self._expect_args(args, 1)
                return self.manager.mkdir(args[0])
            case 'rmdir':
                self._expect_args(args, 1)
                return self.manager.rmdir(args[0])
            case 'touch':
                self._expect_args(args, 1)
                return self.manager.touch(args[0])
            case 'cat':
                self._expect_args(args, 1)
                return self.manager.cat(args[0])
            case 'write':
                self._expect_args(args, 2)
                return self.manager.write(args[0], ' '.join(args[1:]))
            case 'append':
                self._expect_args(args, 2)
                return self.manager.append(args[0], ' '.join(args[1:]))
            case 'rm':
                self._expect_args(args, 1)
                return self.manager.rm(args[0])
            case 'cp':
                self._expect_args(args, 2)
                return self.manager.cp(args[0], args[1])
            case 'mv':
                self._expect_args(args, 2)
                return self.manager.mv(args[0], args[1])
            case 'rename':
                self._expect_args(args, 2)
                return self.manager.rename(args[0], args[1])
            case 'info':
                self._expect_args(args, 1)
                return self.manager.info(args[0])
            case 'exit':
                raise SystemExit
            case _:
                raise InvalidCommandError('Неизвестная команда. Введите help для списка команд.')

    @staticmethod
    def _expect_args(args: list[str], minimum: int) -> None:
        if len(args) < minimum:
            raise InvalidCommandError('Недостаточно аргументов для команды.')

    def run(self) -> None:
        print('Файловый менеджер запущен. Введите help для списка команд.')
        while True:
            try:
                prompt = f'[{self.manager.pwd()}] > '
                command_line = input(prompt)
                result = self.execute(command_line)
                if result:
                    print(result)
            except SystemExit:
                print('Завершение работы.')
                break
            except FileManagerError as error:
                print(error)
            except Exception as error:  # noqa: BLE001
                print(f'Непредвиденная ошибка: {error}')
