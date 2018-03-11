import os
from pathlib import Path
from os.path import relpath


class SgitException(Exception):
    pass


class Repository(object):
    REPO_DIRECTORY_NAME = '.sgit'

    def __init__(self, home):
        self.home = home
        self.repo_dir = os.path.join(home, self.REPO_DIRECTORY_NAME)
        self.objects_dir = os.path.join(self.repo_dir, 'objects')
        self.head_file = os.path.join(self.repo_dir, 'HEAD')
        self.index_file = os.path.join(self.repo_dir, 'index')

    @property
    def dir(self):
        return self.repo_dir

    def check_repository_dir(self):
        return os.path.exists(self.repo_dir)

    def init(self):
        if self.check_repository_dir():
            raise SgitException('Already an sgit repo')

        dirs_to_create = [
            self.repo_dir,
            self.objects_dir
        ]

        files_to_create = [
            self.head_file,
            self.index_file,
        ]

        for directory in dirs_to_create:
            Path(directory).mkdir(exist_ok=True)

        for file in files_to_create:
            Path(file).touch(exist_ok=True)

    def get_relative_paths(self, files):
        return [relpath(f, self.home) for f in files]

    def get_index(self):

        def read_index(line):
            return line.split(' ')[0]

        files = [read_index(line) for line in Path(self.index_file).read_text(encoding='utf-8').split('\n')]
        return self.get_relative_paths(files)

    def get_working_directory(self):
        files = [str(file) for file in Path(self.home).rglob('*')
                 if file.samefile(self.repo_dir) is False
                 and Path(self.repo_dir) not in file.parents
                 and file.is_file()
                 ]
        return self.get_relative_paths(files)

    def status(self):

        working_files = self.get_working_directory()
        staged = self.get_index()
        not_staged = list(set(working_files) - set(staged))

        return {
            'staged': staged,
            'not_staged': not_staged
        }
