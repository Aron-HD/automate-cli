import click
from automate.service import weather


class Context:
    """docstring for Context"""

    def __init__(self, location):
        self.location = location
        self.weather = weather.Weather()


@click.group()
@click.option('-l', '--location', type=str, help='Weather at this location.')
@click.pass_context
def cli(ctx, location):
    """Weather info."""
    click.echo('Weather.py inititated')
    ctx.obj = Context(location)


@cli.command()
@click.pass_context
def current(ctx):
    pass


@cli.command()
@click.pass_context
def forecast(ctx):
    pass
