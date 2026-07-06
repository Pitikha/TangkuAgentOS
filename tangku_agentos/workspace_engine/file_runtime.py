from __future__ import annotations

from .models import Directory, File, FileIndex, Dependency


class FileManager:
    """Manage file instances and basic metadata."""

    def __init__(self) -> None:
        self._files: dict[str, File] = {}

    def create_file(self, file: File) -> None:
        self._files[file.file_id] = file

    def get_file(self, file_id: str) -> File:
        file = self._files.get(file_id)
        if file is None:
            raise KeyError(file_id)
        return file

    def list_files(self) -> list[File]:
        return list(self._files.values())


class DirectoryManager:
    """Manage directory trees and basic traversal."""

    def __init__(self) -> None:
        self._directories: dict[str, Directory] = {}

    def create_directory(self, directory: Directory) -> None:
        self._directories[directory.directory_id] = directory

    def get_directory(self, directory_id: str) -> Directory:
        directory = self._directories.get(directory_id)
        if directory is None:
            raise KeyError(directory_id)
        return directory


class FileIndexManager:
    """Track indexed files and their relationships."""

    def __init__(self) -> None:
        self._indices: dict[str, FileIndex] = {}

    def index(self, file_index: FileIndex) -> None:
        self._indices[file_index.index_id] = file_index

    def get(self, index_id: str) -> FileIndex:
        index = self._indices.get(index_id)
        if index is None:
            raise KeyError(index_id)
        return index


class FileCache:
    """Cache file objects by path."""

    def __init__(self) -> None:
        self._cache: dict[str, File] = {}

    def get(self, path: str) -> File | None:
        return self._cache.get(path)

    def put(self, file: File) -> None:
        self._cache[file.path] = file


class FileMetadataManager:
    """Store metadata for files."""

    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, object]] = {}

    def update(self, file_id: str, metadata: dict[str, object]) -> None:
        self._metadata[file_id] = dict(metadata)

    def get(self, file_id: str) -> dict[str, object]:
        return dict(self._metadata.get(file_id, {}))


class FileWatcher:
    """Abstraction for file change notification without OS-specific implementation."""

    def watch(self, path: str) -> None:
        return None


class FileOperationsCoordinator:
    """Coordinate file operations at a high level."""

    def __init__(self) -> None:
        self._files: dict[str, File] = {}

    def register(self, file: File) -> None:
        self._files[file.file_id] = file

    def get(self, file_id: str) -> File:
        file = self._files.get(file_id)
        if file is None:
            raise KeyError(file_id)
        return file
