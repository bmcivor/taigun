from typing import Optional

import typer

from taigun.config import ConfigManager, Profile
from taigun.db.connection import ConnectionManager

app = typer.Typer(help="Write Taiga tickets directly to the database.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def configure(
    profile: Optional[str] = typer.Option(None, "--profile", help="Profile name to configure."),
) -> None:
    """Set up a connection profile."""
    config = ConfigManager()

    if profile is None:
        profile = typer.prompt("Profile name", default="default")

    if _profile_exists(config, profile):
        overwrite = typer.confirm(f"Profile '{profile}' already exists. Overwrite?", default=False)
        if not overwrite:
            raise typer.Exit()

    host = typer.prompt("Host")
    port = typer.prompt("Port", default=5432)
    database = typer.prompt("Database", default="taiga")
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)
    acting_user = typer.prompt("Acting user")

    new_profile = Profile(
        host=host,
        port=int(port),
        database=database,
        username=username,
        password=password,
        acting_user=acting_user,
    )

    typer.echo("Testing connection...")
    try:
        with ConnectionManager(new_profile).connect():
            pass
    except SystemExit as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    config.save(new_profile, name=None if profile == "default" else profile)
    typer.echo(f"Profile '{profile}' saved.")


def _profile_exists(config: ConfigManager, profile: str) -> bool:
    try:
        config.load(None if profile == "default" else profile)
        return True
    except SystemExit:
        return False
