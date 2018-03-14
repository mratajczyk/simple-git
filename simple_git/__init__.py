# coding=utf-8
import datetime
import hashlib
import os
import shelve
import shutil
import uuid
from logging import Logger
from operator import itemgetter
from os.path import relpath
from pathlib import Path


def md5(value: str):
    return hashlib.md5(value.encode()).hexdigest()


class SgitException(Exception):
    pass


class Repository(object):
    REPO_DIRECTORY_NAME = '.sgit'

    def __init__(self, home: str, logger: Logger):
        self.home = home
        self.logger = logger
        self.repo_dir = Path(home, self.REPO_DIRECTORY_NAME)
        self.objects_dir = Path(self.repo_dir, 'objects')
        self.staging_dir = Path(self.repo_dir, 'staging')
        self.head_file = Path(self.repo_dir, 'HEAD')
        if self.repo_dir.is_dir():
            db_file = str(Path(self.repo_dir, 'index'))
            self.index = shelve.open(db_file, writeback=True)

    @property
    def dir(self):
        return self.repo_dir

    @property
    def index_keys(self):
        return list(self.index.keys())

    def check_repository_dir(self):
        return os.path.exists(str(self.repo_dir))

    def init(self):
        if self.check_repository_dir():
            message = 'Repository directory already exists: {}' \
                .format(self.repo_dir)
            self.logger.debug(message)
            raise SgitException('Already an sgit repo')

        dirs_to_create = [
            self.repo_dir,
            self.objects_dir,
            self.staging_dir,
        ]

        files_to_create = [
            self.head_file,
        ]

        for directory in dirs_to_create:
            Path(directory).mkdir(exist_ok=True)
            self.logger.debug('Created repo directory: {}'.format(directory))

        for file in files_to_create:
            Path(file).touch(exist_ok=True)
            self.logger.debug('Created repo file: {}'.format(file))

    def is_workdir_file(self, file: Path):
        return file.samefile(self.repo_dir) is False \
               and Path(self.repo_dir) not in file.parents \
               and file.is_file()

    def get_relative_path(self, file_name: str):
        return relpath(file_name, str(self.home))

    def get_relative_paths(self, files: list):
        return [self.get_relative_path(f) for f in files]

    def get_working_directory(self):
        files = [str(file) for file in Path(self.home).rglob('*')
                 if self.is_workdir_file(file)]
        self.logger.debug('Files in working directory: {}'.format(len(files)))
        return self.get_relative_paths(files)

    def status(self):
        staged_files = self.index_keys
        diff = list(set(self.get_working_directory()) - set(staged_files))
        not_staged = [(x, 'not staged') for x in diff]

        for staged_file in staged_files:

            working_file = Path(self.home, staged_file)
            staged_file_path = Path(self.staging_dir, self.index[staged_file])

            working_version = md5(working_file.read_text())
            staged_version = md5(staged_file_path.read_text())

            if working_version != staged_version:
                not_staged.append((staged_file, 'modified'))

        return {
            'staged': [(x, '') for x in staged_files],
            'not_staged': not_staged
        }

    def set_index(self, files: list):
        for to_index in files:
            assert len(to_index) == 3
            file_name, staged_file_name, content = to_index
            Path(self.staging_dir, staged_file_name).write_text(content)
            self.index[file_name] = staged_file_name
            self.logger.debug('Added file to staging: {}'.format(file_name))
        count_keys = len(self.index_keys)
        self.logger.debug('Files in staging: {}'.format(count_keys))

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
                text = add_file.read_text()
                hash_name = md5(str(add_file))
                hash_content = md5(text)
                staged_file_name = '_'.join([hash_name, hash_content])
                to_index.append((self.get_relative_path(add_file),
                                 staged_file_name,
                                 text))
        self.set_index(to_index)

        if len(to_index) == 0:
            self.logger.debug('File not found: {}'.format(str(path_object)))
            message = 'pathspec \'{}\' did not match any files' \
                .format(add_path)
            raise SgitException(message)

    def can_commit(self):
        return len(self.index_keys) > 0

    def commit(self, message: str):
        if len(message.strip()) == 0:
            raise SgitException('Empty commit message')

        if self.can_commit() is False:
            raise SgitException('Nothing to commit')

        commit = str(uuid.uuid4())[:8]
        commit_dir = Path(self.objects_dir, commit)
        commit_dir.mkdir()

        meta_db = str(Path(commit_dir, 'meta'))
        commit_meta = shelve.open(meta_db, writeback=True)
        commit_meta['id'] = commit
        commit_meta['message'] = message
        commit_meta['time'] = datetime.datetime.now()
        commit_meta['index'] = dict(self.index)

        self.logger.debug('Commiting: {}'.format(str(dict(commit_meta))))

        for file, staging_name in commit_meta['index'].items():
            source = Path(self.staging_dir, staging_name)
            target = Path(commit_dir, staging_name)
            shutil.copy(str(source), str(target))
            os.remove(str(source))
            self.logger.debug('Removed staging file: {}'.format(str(source)))
            del (self.index[file])
            self.logger.debug('Removed from index: {}'.format(str(file)))

        self.head_file.write_text(commit)

    def log(self):
        commits = []
        for child in self.objects_dir.rglob('*'):
            if child.name == 'meta':
                commits.append(dict(shelve.open(str(child))))
        self.logger.debug('Log: {}'.format(str(commits)))
        return sorted(commits, key=itemgetter('time'))[::-1]
