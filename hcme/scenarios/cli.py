import click

from hcme import config

from .reactor import ScenarioReactor


@click.group()
def main():
    """Manage HCME scenario outputs."""
    pass


@main.command()
@click.argument("name")
@click.argument("output_dir", default=None)
def reactor(name, output_dir):
    """Create all required scenario inputs for the input scenairo."""
    senario_reactor = ScenarioReactor(name)
    # Get default output dir from settings
    if not output_dir:
        base_dir = config.get("scenario_inputs")
        output_dir = base_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)
    senario_reactor.generate(output_dir=output_dir)


@main.command()
@click.argument("name")
def run(name):
    """Run a scenario by name."""
    pass


if __name__ == "__main__":
    main()
