import re
import os

import psutil
import artifacts

from dfvfs.path import factory
from dfvfs.lib import definitions
from dfvfs.resolver import resolver

from fastir.common.logging import logger
from fastir.common.collector import AbstractCollector
from fastir.common.path_components import RecursionPathComponent, GlobPathComponent, RegularPathComponent, PathObject

CHUNK_SIZE = 5 * 1024 * 1024
PATH_RECURSION_REGEX = re.compile(r"\*\*(?P<max_depth>\d*)")
PATH_GLOB_REGEX = re.compile(r"\*|\?|\[.+\]")

TSK_FILESYSTEMS = ['NTFS', 'ext3', 'ext4']
APFS_FILESYSTEMS = ['apfs']


class FileSystem:
    def __init__(self):
        self._patterns = []

    def add_pattern(self, artifact, pattern):
        self._patterns.append({
            'artifact': artifact,
            'pattern': pattern
        })

    def _relative_path(self, filepath):
        raise NotImplementedError

    def _parse(self, pattern):
        components = []

        items = pattern.split('/')
        for i, item in enumerate(items):
            # Search for '**' glob recursion
            recursion = PATH_RECURSION_REGEX.search(item)
            if recursion:
                max_depth = None

                if recursion.group('max_depth'):
                    max_depth = int(recursion.group('max_depth'))

                components.append(RecursionPathComponent(i < (len(items) - 1), max_depth))
            else:
                glob = PATH_GLOB_REGEX.search(item)
                if glob:
                    components.append(GlobPathComponent(i < (len(items) - 1), item))
                else:
                    components.append(RegularPathComponent(i < (len(items) - 1), item))

        return components

    def _base_generator(self):
        raise NotImplementedError

    def collect(self, output):
        for pattern in self._patterns:
            logger.debug("Collecting pattern '{}' for artifact '{}'".format(pattern['pattern'], pattern['artifact']))

            # Normalize the pattern, relative to the mountpoint
            relative_pattern = self._relative_path(pattern['pattern'])
            path_components = self._parse(relative_pattern)

            generator = self._base_generator
            for component in path_components:
                generator = component.get_generator(generator)

            for path in generator():
                if path.is_file():
                    output.add_collected_file(pattern['artifact'], path)


class DFVFSFileSystem(FileSystem):
    def __init__(self, path):
        super().__init__()

        self._path = path

        # Should be defined in subclasses
        self._base_path_spec = None

        # Cache parsed entries for better performances
        self._entries_cache = {}
        self._entries_cache_last = []

    def _relative_path(self, filepath):
        normalized_path = filepath.replace(os.path.sep, '/')
        return normalized_path[len(self._path):].lstrip('/')

    def _base_generator(self):
        file_entry = resolver.Resolver.OpenFileEntry(self._base_path_spec)

        yield PathObject(self, os.path.basename(self._path), self._path, file_entry)

    def is_directory(self, path):
        return path.obj.IsDirectory()

    def is_file(self, path):
        return path.obj.IsFile()

    def get_path(self, parent, name):
        for path_object in self.list_directory(parent):
            if os.path.normcase(name) == os.path.normcase(path_object.name):
                return path_object

    def list_directory(self, path_object):
        if path_object.path in self._entries_cache:
            return self._entries_cache[path_object.path]
        else:
            # Make sure we do not keep more than 10 000 entries in the cache
            if len(self._entries_cache_last) >= 10000:
                first = self._entries_cache_last.popleft()
                del self._entries_cache[first]

            entries = []

            if not self.is_directory(path_object):
                return

            directory = path_object.obj
            for entry in directory.sub_file_entries:
                name = entry.name
                filepath = os.path.join(path_object.path, name)
                entry_path_object = PathObject(self, name, filepath, entry)

                if entry.IsLink():
                    symlink_object = self._follow_symlink(path_object, entry_path_object)

                    if symlink_object:
                        entries.append(symlink_object)
                else:
                    entries.append(entry_path_object)

            self._entries_cache[path_object.path] = entries
            self._entries_cache_last.append(entries)

            return entries

    def _follow_symlink(self, parent, path_object):
        # TODO: attempt to follow symlinks with DFVFS
        #
        # As a temporary fix, downgrade all links to OSFileSystem so that
        # they are still collected
        return OSFileSystem('/').get_fullpath(path_object.path)

    def get_size(self, path_object):
        stream = path_object.obj.GetFileObject()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.close()

        return size

    def read_chunks(self, path_object):
        stream = path_object.obj.GetFileObject()

        chunk = stream.read(CHUNK_SIZE)
        if chunk:
            yield chunk

        stream.close()


class DFVFSParsedFileSystem(DFVFSFileSystem):
    # Should be defined by subclasses
    fs_type = None

    def __init__(self, path, device):
        super().__init__(path)

        # Unix Device
        if path.startswith('/'):
            self._device = device
        else:
            # On Windows, we need a specific format '\\.\<DRIVE_LETTER>:'
            self._device = r"\\.\{}:".format(device[0])

        self._os_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_OS, location=self._device)
        self._base_path_spec = factory.Factory.NewPathSpec(self.fs_type, location='/', parent=self._os_path_spec)

    def get_fullpath(self, fullpath):
        relative_path = '/' + self._relative_path(fullpath)
        path_spec = factory.Factory.NewPathSpec(self.fs_type, location=relative_path, parent=self._os_path_spec)
        file_entry = resolver.Resolver.OpenFileEntry(path_spec)

        return PathObject(self, os.path.basename(fullpath), fullpath, file_entry)


class TSKFileSystem(DFVFSParsedFileSystem):
    fs_type = definitions.TYPE_INDICATOR_TSK


class APFSFileSystem(DFVFSParsedFileSystem):
    fs_type = definitions.TYPE_INDICATOR_APFS


class OSFileSystem(DFVFSFileSystem):
    def __init__(self, path):
        super().__init__(path)

        self._base_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_OS, location=path)

    def get_fullpath(self, fullpath):
        path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_OS, location=fullpath)
        file_entry = resolver.Resolver.OpenFileEntry(path_spec)

        return PathObject(self, os.path.basename(fullpath), fullpath, file_entry)

    def is_file(self, path):
        """Symlinks are automatically resolved by OS"""
        return path.obj.IsFile() or path.obj.IsLink()


class FileSystemManager(AbstractCollector):
    def __init__(self):
        self._filesystems = {}
        self._mount_points = psutil.disk_partitions(True)

    def _get_mountpoint(self, filepath):
        best_mountpoint = None
        best_mountpoint_length = 0

        for mountpoint in self._mount_points:
            if filepath.startswith(mountpoint.mountpoint):
                if len(mountpoint.mountpoint) > best_mountpoint_length:
                    best_mountpoint = mountpoint
                    best_mountpoint_length = len(mountpoint.mountpoint)

        if best_mountpoint is None:
            raise IndexError(f'Could not find a mountpoint for path {filepath}')

        return best_mountpoint

    def _get_filesystem(self, filepath):
        # Fetch the mountpoint for this particular path
        mountpoint = self._get_mountpoint(filepath)

        # Fetch or create the matching filesystem
        if mountpoint.mountpoint not in self._filesystems:
            if mountpoint.fstype in TSK_FILESYSTEMS:
                self._filesystems[mountpoint.mountpoint] = TSKFileSystem(mountpoint.mountpoint, mountpoint.device)
            elif mountpoint.fstype in APFS_FILESYSTEMS:
                self._filesystems[mountpoint.mountpoint] = APFSFileSystem(mountpoint.mountpoint, mountpoint.device)
            else:
                self._filesystems[mountpoint.mountpoint] = OSFileSystem(mountpoint.mountpoint)

        return self._filesystems[mountpoint.mountpoint]

    def add_pattern(self, artifact, pattern):
        pattern = os.path.normpath(pattern)

        # If the pattern starts with '\', it should be applied to all drives
        if pattern.startswith('\\'):
            for mountpoint in self._mount_points:
                if mountpoint.fstype in TSK_FILESYSTEMS:
                    extended_pattern = os.path.join(mountpoint.mountpoint, pattern[1:])
                    filesystem = self._get_filesystem(extended_pattern)
                    filesystem.add_pattern(artifact, extended_pattern)

        else:
            filesystem = self._get_filesystem(pattern)
            filesystem.add_pattern(artifact, pattern)

    def collect(self, output):
        for path in list(self._filesystems):
            logger.debug(f"Start collection for '{path}'")
            self._filesystems[path].collect(output)

    def register_source(self, artifact_definition, artifact_source, variables):
        supported = False

        if artifact_source.type_indicator == artifacts.definitions.TYPE_INDICATOR_FILE:
            supported = True

            for p in artifact_source.paths:
                for sp in variables.substitute(p):
                    self.add_pattern(artifact_definition.name, sp)

        return supported

    def get_path_object(self, filepath):
        filesystem = self._get_filesystem(filepath)
        return filesystem.get_fullpath(filepath)
