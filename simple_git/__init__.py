import hashlib
import os
from os.path import relpath
from pathlib import Path


def md5(value: str):
    return hashlib.md5(value.encode('utf-8')).hexdigest()


class SgitException(Exception):
    pass


class Repository(object):
    REPO_DIRECTORY_NAME = '.sgit'

    def __init__(self, home: str):
        self.home = home
        self.repo_dir = Path(home, self.REPO_DIRECTORY_NAME)
        self.objects_dir = Path(self.repo_dir, 'objects')
        self.staging_dir = Path(self.repo_dir, 'staging')
        self.head_file = Path(self.repo_dir, 'HEAD')
        self.index_file = Path(self.repo_dir, 'index')

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
            self.objects_dir,
            self.staging_dir,
        ]

        files_to_create = [
            self.head_file,
            self.index_file,
        ]

        for directory in dirs_to_create:
            Path(directory).mkdir(exist_ok=True)

        for file in files_to_create:
            Path(file).touch(exist_ok=True)

    def is_workdir_file(self, file: Path):
        return file.samefile(self.repo_dir) is False and Path(self.repo_dir) not in file.parents and file.is_file()

    def get_relative_path(self, file_name: str):
        return relpath(file_name, self.home)

    def get_relative_paths(self, files: list):
        return [self.get_relative_path(f) for f in files]

    def get_index(self):

        def read_index(line: str):
            result = None
            try:
                file, staged_file_name = line.split('\t')
                content = staged_file_name.split('_')[1]
                result = {'file': file, 'content': content, 'staged_file_name': staged_file_name}
            except ValueError:
                pass
            return result

        index_file_content = Path(self.index_file).read_text(encoding='utf-8').split('\n')
        files = [read_index(line) for line in index_file_content if read_index(line) is not None]
        return files

    def get_working_directory(self):
        files = [str(file) for file in Path(self.home).rglob('*')
                 if self.is_workdir_file(file)]
        return self.get_relative_paths(files)

    def status(self):

        working_files = self.get_working_directory()
        staged = self.get_index()
        staged_list = [x.get('file') for x in staged if 'file' in x]
        not_staged = [(x, 'not staged') for x in list(set(working_files) - set(staged_list))]

        for staged_file in staged:
            working_version = md5(Path(self.home, staged_file.get('file')).read_text())
            if working_version != staged_file.get('content'):
                not_staged.append((staged_file.get('file'), 'modified'))

        return {
            'staged': [(x.get('file'), '') for x in staged if 'file' in x],
            'not_staged': not_staged
        }

    def set_index(self, files: list):

        actual_index = self.get_index()

        for to_index in files:
            assert len(to_index) == 3
            file_name, staged_file_name, content = to_index
            Path(self.staging_dir, staged_file_name).write_text(content)
            try:
                check = next(x for x in actual_index if x.get('file') == file_name)
                idx = actual_index.index(check)
                actual_index[idx]['staged_file_name'] = staged_file_name
            except StopIteration:
                actual_index.append({'file': file_name, 'staged_file_name': staged_file_name})

        index_content = '\n'.join([x.get('file') + '\t' + x.get('staged_file_name') for x in actual_index])
        Path(self.index_file).write_text(index_content)

    def add(self, add_path: str):
        to_add = []
        to_index = []
        path_object = Path(self.home, add_path)

        if path_object.is_file():
            to_add.append(path_object)

        if path_object.is_dir():
            for child in path_object.rglob('*'):
                to_add.append(child)

        for add_file in to_add:
            if self.is_workdir_file(add_file):
                hash_name = md5(str(add_file))
                hash_content = md5(add_file.read_text())
                staged_file_name = '_'.join([hash_name, hash_content])
                to_index.append((self.get_relative_path(add_file), staged_file_name, add_file.read_text()))
        self.set_index(to_index)
