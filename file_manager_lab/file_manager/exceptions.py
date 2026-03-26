class FileManagerError(Exception):
    """Базовое исключение файлового менеджера."""


class PathOutsideWorkspaceError(FileManagerError):
    """Попытка выйти за пределы рабочей директории."""


class InvalidCommandError(FileManagerError):
    """Неизвестная или некорректная команда."""
