import click
import os
from simple_git import Repository, SgitException


def format_error(message: str):
    return click.style(message, bg='red', fg='white')


def format_ok(message: str):
    return click.style(message, fg='green')


def format_important(message: str):
    return click.style(message, bold=True)


def echo(message: str):
    click.echo(message)


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    home = os.environ['SGIT_DIR'] if os.environ.get('SGIT_DIR') else os.getcwd()
    ctx.obj = Repository(home=home)
    if ctx.obj.check_repository_dir() is False and ctx.invoked_subcommand != 'init':
        raise click.UsageError(format_error('Not a sgit repository, use sgit init'))


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
    repo.add(path)


@cli.command()
@click.pass_obj
def commit():
    pass


@cli.command()
@click.pass_obj
def status(repo: Repository):
    repo_status = repo.status()
    types = [
        {'key': 'staged', 'message': 'Changes to be committed:'},
        {'key': 'not_staged', 'message': 'Changes not staged for commit:'}
    ]

    for file_type in types:
        if len(repo_status.get(file_type.get('key'))) > 0:
            echo(format_important(file_type.get('message')))
            for file in repo_status.get(file_type.get('key')):
                echo(' '.join([format_ok(file[1]), file[0]]))


cli.add_command(init)
cli.add_command(add)
cli.add_command(commit)
cli.add_command(status)

if __name__ == '__main__':
    cli()
