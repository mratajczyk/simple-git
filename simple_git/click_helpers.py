# coding=utf-8
import click


def format_error(message: str):
    return click.style(message, fg='red')


def format_ok(message: str):
    return click.style(message, fg='green')


def format_important(message: str):
    return click.style(message, bold=True)


def echo(message: str):
    click.echo(message)
