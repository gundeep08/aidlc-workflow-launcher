import click

from cli.commands.init import init
from cli.commands.clone import clone
from cli.commands.start import start
from cli.commands.status import status
from cli.commands.resume import resume
from cli.commands.update_rules import update_rules
from cli.commands.update_docs import update_docs
from cli.commands.update import update
from cli.commands.re import re_skills


@click.group()
def cli():
    """AI-DLC Workflow Launcher CLI."""


cli.add_command(init)
cli.add_command(clone)
cli.add_command(start)
cli.add_command(status)
cli.add_command(resume)
cli.add_command(update)
cli.add_command(update_rules)
cli.add_command(update_docs)
cli.add_command(re_skills)

if __name__ == "__main__":
    cli()
