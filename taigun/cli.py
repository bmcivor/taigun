from pathlib import Path
from typing import List, Optional

import typer

from taigun.config import ConfigManager, Profile
from taigun.db.connection import ConnectionManager
from taigun.db.epic import EpicWriter
from taigun.db.issue import IssueWriter
from taigun.db.lister import Lister
from taigun.db.story import StoryWriter
from taigun.db.task import TaskWriter
from taigun.exceptions import ResolveError
from taigun.parsers.file import FileParser
from taigun.resolver import Resolver

_WRITERS = {
    "story": StoryWriter,
    "issue": IssueWriter,
    "task": TaskWriter,
    "epic": EpicWriter,
}

app = typer.Typer(help="Write Taiga tickets directly to the database.")

projects_app = typer.Typer(help="List and inspect projects.")
epics_app = typer.Typer(help="List and inspect epics.")
statuses_app = typer.Typer(help="List and inspect statuses.")

app.add_typer(projects_app, name="projects")
app.add_typer(epics_app, name="epics")
app.add_typer(statuses_app, name="statuses")


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


@app.command()
def push(
    files: List[Path] = typer.Argument(..., help="Ticket file(s) to push."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Resolve FKs but do not insert."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """Parse and push one or more ticket files to Taiga."""
    config = ConfigManager().load(profile)
    parser = FileParser()
    manager = ConnectionManager(config)
    any_failed = False

    for path in files:
        try:
            ticket = parser.parse(path)
            ticket_type = type(ticket).__name__.lower()
            writer_class = _WRITERS[ticket_type]

            with manager.connect(dry_run=dry_run) as conn:
                resolver = Resolver(conn)
                writer = writer_class(conn, resolver)
                ref = writer.write(ticket, config.acting_user)

        except Exception as e:
            typer.echo(f"✗ {Path(path).name}: {e}", err=True)
            any_failed = True
            continue

        if dry_run:
            typer.echo(f"~ {ticket_type}: \"{ticket.subject}\"")
        else:
            typer.echo(f"✓ #{ref} {ticket_type}: \"{ticket.subject}\"")

    if any_failed:
        raise typer.Exit(code=1)


@projects_app.command("list")
def projects_list(
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List all projects on the configured instance."""
    config = ConfigManager().load(profile)
    with ConnectionManager(config).connect() as conn:
        lister = Lister(conn)
        projects = lister.list_projects()

    for name, slug in projects:
        typer.echo(f"{name} ({slug})")


@epics_app.command("list")
def epics_list(
    project_slug: str = typer.Argument(..., help="Project slug."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List all epics in a project."""
    config = ConfigManager().load(profile)
    with ConnectionManager(config).connect() as conn:
        resolver = Resolver(conn)
        lister = Lister(conn)
        try:
            project_id = resolver.resolve_project(project_slug)
        except ResolveError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=1)

        epics = lister.list_epics(project_id)

    for ref, subject in epics:
        typer.echo(f"#{ref}  {subject}")


@statuses_app.command("list")
def statuses_list(
    project_slug: str = typer.Argument(..., help="Project slug."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List statuses grouped by ticket type for a project."""
    config = ConfigManager().load(profile)
    with ConnectionManager(config).connect() as conn:
        resolver = Resolver(conn)
        lister = Lister(conn)
        try:
            project_id = resolver.resolve_project(project_slug)
        except ResolveError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=1)

        statuses = lister.list_statuses(project_id)

    for ticket_type, status_list in statuses.items():
        typer.echo(f"{ticket_type}:")
        for name, is_closed in status_list:
            suffix = "  [closed]" if is_closed else ""
            typer.echo(f"  {name}{suffix}")


def _profile_exists(config: ConfigManager, profile: str) -> bool:
    try:
        config.load(None if profile == "default" else profile)
        return True
    except SystemExit:
        return False
