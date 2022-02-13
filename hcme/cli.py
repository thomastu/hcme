from pathlib import Path

import click
import invoke
import sqlalchemy as sa

from hcme import config
from hcme.beam import wrapper as beam_wrapper
from hcme.db import Session, models
from hcme.metrics import export as export_metrics
from hcme.scenarios import cli as scenarios_cli

_here = Path(__file__).resolve()

alembic = _here.parent / "db/alembic.ini"

CONTEXT_SETTINGS = {
    "ignore_unknown_options": True,
    "help_option_names": list(),
    "allow_interspersed_args": False,
}


@click.group()
def main():
    """HCME management command."""
    pass


def cli_proxy_factory(alias, command, help_text="", env_vars={}):
    """Factory to enable forwarding click commands to hard-to-remember alembic and uvicorn commands.

    Args:
        command: Name of the command to forward.
    """

    help_text = help_text or f"Proxy for `{command}`"

    @click.command(name=alias, context_settings=CONTEXT_SETTINGS, help=help_text)
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    def proxy(args):
        args = " ".join(map(lambda x: f'"{x}"' if not x.startswith("-") else x, args))
        cmd = f"{command} {args}".strip()
        click.echo(f"Running : {cmd}")
        invoke.run(cmd, env=env_vars)

    main.add_command(proxy)


main.add_command(beam_wrapper.main, name="beam")
main.add_command(scenarios_cli.main, name="scenario")


@main.group(invoke_without_command=True)
@click.pass_context
def metrics(ctx):
    if ctx.invoked_subcommand is None:
        session = Session()
        metrics = session.execute(sa.select(models.Metrics).order_by("domain"))
        _domain = ""
        for (metric,) in metrics:
            if metric.domain != _domain:
                click.echo("=" * 15)
                click.echo(f"Domain: {metric.domain}")
                click.echo("-" * 15)
            click.echo(f"{metric.name}: {metric.description}")
            _domain = metric.domain


@metrics.command()
@click.option("-d", "--domain")
@click.option("-n", "--name", default="")
@click.option("-h", "--hooks", default=["csv"], multiple=True)
def export(domain, name, hooks):
    """Export metrics"""
    export_metrics(domain=domain, name=name, default_hooks=hooks)


cli_proxy_factory("alembic", f"alembic -c {alembic}")
cli_proxy_factory("migrate", f"alembic -c {alembic} upgrade head")
cli_proxy_factory("makemigrations", f"alembic -c {alembic} revision --autogenerate")
cli_proxy_factory(
    "install_kernel",
    f"python -m ipykernel install --user --name=hcme",
    "Install the current virtualenv as an ipython kernel for hcme.",
)
