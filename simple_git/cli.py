#!/usr/bin/env python3
# coding=utf-8
import logging
import os

import click
from simple_git.click_helpers import format_error, format_important, format_ok, echo
from simple_git.repository import Repository, SgitException


@click.group()
@click.pass_context
@click.option('--debug/--no-debug', default=False)
def cli(ctx: click.Context, debug):
    logger = logging.getLogger(__name__)

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    home = os.environ['SGIT_DIR'] \
        if os.environ.get('SGIT_DIR') else os.getcwd()

    ctx.obj = Repository(home=home, logger=logger)
    if ctx.obj.check_repository_dir() \
            is False and ctx.invoked_subcommand != 'init':
        error = format_error('Not a sgit repository, use sgit init')
        raise click.UsageError(error)


@cli.command()
@click.pass_obj
def init(repo: Repository):
    try:
        repo.init()
        echo(format_ok('Repository created at {}'.format(repo.dir)))
    except SgitException as e:
        echo(format_error(str(e)))


@cli.command()
@click.argument('path')
@click.pass_obj
def add(repo: Repository, path: str):
    try:
        repo.add(path)
    except SgitException as e:
        echo(format_error(str(e)))


@cli.command()
@click.option('--message', '-m')
@click.pass_obj
def commit(repo: Repository, message: str):
    if message is None:
        editor_top = '# Put commit message above this line\n'
        editor_message = click.edit('\n\n' + editor_top)
        if editor_message is not None:
            message = editor_message.split(editor_top, 1)[0].rstrip('\n')
    try:
        repo.commit(message)
    except SgitException as e:
        echo(format_error(str(e)))


@cli.command()
@click.pass_obj
def log(repo: Repository):
    for row in repo.log():
        echo('\t'.join([format_important(row['id']), str(row['time'])]))
        echo(row['message'].strip())
        echo('\n' * 2)


@cli.command()
@click.pass_obj
def status(repo: Repository):
    repo_status = repo.status()
    types = [
        {'key': 'staged', 'message': 'Changes to be committed:'},
        {'key': 'not_staged', 'message': 'Changes not staged for commit:'}
    ]
    for file_type in types:
        key = file_type['key']
        message = file_type.get('message')
        if len(repo_status[key]) > 0:
            echo(format_important(message))
            for file in repo_status[key]:
                file_info, file_name = file
                echo(' '.join([format_ok(file_info), file_name]))


cli.add_command(init)
cli.add_command(add)
cli.add_command(commit)
cli.add_command(status)

if __name__ == '__main__':
    cli()
