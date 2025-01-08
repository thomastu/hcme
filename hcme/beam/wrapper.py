import os
from pathlib import Path
from subprocess import call

import click

from hcme.config import beam_conf, beam_dir, java_exec_path


def build_cmd(conf, maxram=2):
    """Format the command for running a BEAM iteration."""

    cmd = (
        f"{java_exec_path} -Dorg.gradle.appname={beam_dir}gradlew -classpath {beam_dir}gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :run "
        f"""-PappArgs="['--config', '{conf}']" -PmaxRAM={maxram}"""
    )
    return cmd


def _format_cmd(beam_path, conf):
    c = str(Path(beam_dir).absolute() / "gradlew")
    args = f":run -PappArgs=\"['--config', {conf}]\""
    return [c, args]


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "-c", "--conf", type=click.Path(exists=True), default=beam_conf, show_default=True
)
@click.option("-r", "--max-ram", type=click.INT, help="Max ram to use in GB", default=2)
def main(ctx, conf, max_ram):
    """Wrapper for running BEAM."""
    if ctx.invoked_subcommand is None:
        cmd = build_cmd(conf, max_ram)
        click.echo(cmd)
        call(cmd, shell=True, cwd=str(beam_dir))


@main.command()
@click.option(
    "-c", "--conf", type=click.Path(exists=True), default=beam_conf, show_default=True
)
@click.option("-r", "--max-ram", type=click.INT, help="Max ram to use in GB", default=2)
def info(conf, max_ram):
    """Print gradlew path and BEAM directory."""
    cmd = build_cmd(conf or "<path-to-config.conf>", max_ram)
    click.echo(f"Beam Command: {cmd}")


if __name__ == "__main__":
    main()
