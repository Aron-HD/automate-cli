import click
from pathlib import Path


class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in (Path(__file__).parent.resolve() / 'commands').glob('*.py'):
            if not filename.stem.startswith("__"):
                rv.append(filename.stem)
                # click.echo(filename)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"automate.commands.{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI)
def cli():
    """Welcome to AUTOMATE"""
    pass
