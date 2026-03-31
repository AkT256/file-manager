from __future__ import annotations

from pathlib import Path
import shutil
from typing import Iterable

from .exceptions import FileManagerError, PathOutsideWorkspaceError
import zipfile
from pathlib import Path

class FileManager:
    """Файловый менеджер с ограничением действий внутри workspace."""

    def __init__(self, workspace_root: Path):
        """Инициализирует менеджер с корневой директорией."""
        self.workspace_root = workspace_root.resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.current_dir = self.workspace_root

    def _resolve_path(self, raw_path: str | None = None) -> Path:
        """Преобразует путь в абсолютный путь с проверкой workspace."""
        if not raw_path or raw_path == '.':
            candidate = self.current_dir
        else:
            path = Path(raw_path)
            candidate = (self.current_dir / path).resolve() if not path.is_absolute() else path.resolve()
        self._ensure_inside_workspace(candidate)
        return candidate

    def _ensure_inside_workspace(self, path: Path) -> None:
        """Проверяет, что путь находится внутри workspace."""
        try:
            path.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PathOutsideWorkspaceError(
                'Ошибка: путь находится вне рабочей директории.'
            ) from exc

    def pwd(self) -> str:
        """Возвращает текущую директорию."""
        return str(self.current_dir.relative_to(self.workspace_root)) or '.'

    def ls(self) -> list[str]:
        """Выводит содержимое текущей директории."""
        items = []
        for item in sorted(self.current_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            prefix = '[DIR]' if item.is_dir() else '[FILE]'
            items.append(f'{prefix} {item.name}')
        return items

    def cd(self, raw_path: str) -> str:
        """Переходит в указанную директорию."""
        target = self._resolve_path(raw_path)
        if not target.exists():
            raise FileManagerError('Ошибка: директория не существует.')
        if not target.is_dir():
            raise FileManagerError('Ошибка: указанный путь не является директорией.')
        self.current_dir = target
        return f'Текущая директория: {self.pwd()}'

    def mkdir(self, name: str) -> str:
        """Создаёт новую директорию."""
        path = self._resolve_path(name)
        path.mkdir(parents=True, exist_ok=False)
        return f'Директория создана: {path.name}'

    def rmdir(self, name: str) -> str:
        """Удаляет пустую директорию."""
        path = self._resolve_path(name)
        if not path.exists() or not path.is_dir():
            raise FileManagerError('Ошибка: директория не найдена.')
        path.rmdir()
        return f'Директория удалена: {path.name}'

    def tree(self, start: Path | None = None, prefix: str = '') -> list[str]:
        """Выводит дерево структуры директорий."""
        directory = start or self.current_dir
        entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        lines: list[str] = []
        for index, entry in enumerate(entries):
            connector = '└── ' if index == len(entries) - 1 else '├── '
            lines.append(prefix + connector + entry.name)
            if entry.is_dir():
                extension = '    ' if index == len(entries) - 1 else '│   '
                lines.extend(self.tree(entry, prefix + extension))
        return lines

    def touch(self, name: str) -> str:
        """Создаёт пустой файл."""
        path = self._resolve_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        return f'Файл создан: {path.name}'

    def cat(self, name: str) -> str:
        """Выводит содержимое файла."""
        path = self._resolve_path(name)
        if not path.exists() or not path.is_file():
            raise FileManagerError('Ошибка: файл не найден.')
        return path.read_text(encoding='utf-8')

    def write(self, name: str, content: str) -> str:
        """Записывает содержимое в файл (перезаписывает)."""
        path = self._resolve_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        content_bytes = len(content.encode("utf-8"))
        self.check_quota(content_bytes)
        path.write_text(content, encoding="utf-8")
        return f"Данные записаны в файл: {path.name}"

    def append(self, name: str, content: str) -> str:
        """Добавляет содержимое в конец файла."""
        path = self._resolve_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as file:
            file.write(content)
        return f'Данные добавлены в файл: {path.name}'

    def rm(self, name: str) -> str:
        """Удаляет файл."""
        path = self._resolve_path(name)
        if not path.exists() or not path.is_file():
            raise FileManagerError('Ошибка: файл не найден.')
        path.unlink()
        return f'Файл удалён: {path.name}'

    def cp(self, source: str, destination: str) -> str:
        """Копирует файл или директорию."""
        source_path = self._resolve_path(source)
        destination_path = self._resolve_path(destination)
        if not source_path.exists():
            raise FileManagerError('Ошибка: исходный путь не найден.')

        if source_path.is_dir():
            shutil.copytree(source_path, destination_path)
        else:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
        return f'Скопировано: {source} -> {destination}'

    def mv(self, source: str, destination: str) -> str:
        """Перемещает файл или директорию."""
        source_path = self._resolve_path(source)
        destination_path = self._resolve_path(destination)
        if not source_path.exists():
            raise FileManagerError('Ошибка: исходный путь не найден.')
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination_path))
        return f'Перемещено: {source} -> {destination}'

    def rename(self, source: str, new_name: str) -> str:
        """Переименовывает файл или директорию."""
        source_path = self._resolve_path(source)
        if not source_path.exists():
            raise FileManagerError('Ошибка: исходный путь не найден.')
        target = source_path.with_name(new_name)
        self._ensure_inside_workspace(target.resolve())
        source_path.rename(target)
        return f'Переименовано: {source_path.name} -> {target.name}'

    def info(self, name: str) -> str:
        """Выводит информацию об объекте (файле или директории)."""
        path = self._resolve_path(name)

        if not path.exists():
            raise FileManagerError('Ошибка: объект не найден.')

        item_type = 'директория' if path.is_dir() else 'файл'

        if path.is_file():
            size = path.stat().st_size
        else:
            size = self.get_directory_size(path)

        return (
            f'Имя: {path.name}\n'
            f'Тип: {item_type}\n'
            f'Путь: {path.relative_to(self.workspace_root)}\n'
            f'Размер: {size} байт'
        )

    def help(self) -> str:
        """Выводит список доступных команд."""
        commands: Iterable[str] = (
            'help                              - показать список команд',
            'pwd                               - показать текущую директорию',
            'ls                                - показать содержимое текущей папки',
            'tree                              - показать дерево каталогов',
            'cd <путь>                         - перейти в директорию',
            'mkdir <имя>                       - создать директорию',
            'rmdir <имя>                       - удалить пустую директорию',
            'touch <имя_файла>                 - создать пустой файл',
            'cat <имя_файла>                   - вывести содержимое файла',
            'write <файл> <текст>              - перезаписать файл текстом',
            'append <файл> <текст>             - добавить текст в конец файла',
            'rm <имя_файла>                    - удалить файл',
            'cp <источник> <назначение>        - копировать файл/папку',
            'mv <источник> <назначение>        - переместить файл/папку',
            'rename <источник> <новое_имя>     - переименовать файл/папку',
            'info <имя>                        - показать информацию об объекте',
            'zip <источник> <архив.zip>        - архивировать файл или папку',
            'unzip <архив.zip> [папка]         - распаковать архив',
            'exit                              - выход из программы',
        )
        return '\n'.join(commands)
    
    def zip_item(self, src_path: str, zip_path: str) -> str:
        """Архивирует файл или директорию в ZIP."""
        src = self._resolve_path(src_path)
        zip_path_obj = self._resolve_path(zip_path)

        with zipfile.ZipFile(zip_path_obj, 'w', zipfile.ZIP_DEFLATED) as zf:
            if src.is_file():
                zf.write(src, arcname=src.name)
            else:
                for file in src.rglob('*'):
                    if file.is_file():
                        zf.write(file, arcname=file.relative_to(src))

        return f'Создан архив: {zip_path_obj.name}'


    def unzip_item(self, zip_path: str, extract_to: str = '.') -> str:
        """Распаковывает ZIP архив."""
        zip_path_obj = self._resolve_path(zip_path)
        extract_to_obj = self._resolve_path(extract_to)
        extract_to_obj.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path_obj, 'r') as zf:
            zf.extractall(extract_to_obj)

        return f'Архив распакован в: {extract_to_obj.name}'


    def get_directory_size(self, path: Path | None = None) -> int:
        """Вычисляет общий размер директории."""
        target = path if path is not None else self.workspace_root
        total = 0

        for p in Path(target).rglob('*'):
            if p.is_file():
                total += p.stat().st_size

        return total


    def check_quota(self, new_file_size: int = 0) -> None:
        """Проверяет не превышен ли лимит дискового пространства."""
        from config import MAX_SIZE_MB

        current_size = self.get_directory_size()
        limit = MAX_SIZE_MB * 1024 * 1024

        if current_size + new_file_size > limit:
            raise FileManagerError('Превышен лимит дискового пространства')
        
