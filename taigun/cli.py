from pathlib import Path
from typing import List, Optional

import typer

from taigun.config import ConfigManager, Profile
from taigun.db.connection import ConnectionManager
from taigun.db.epic import EpicWriter
from taigun.db.issue import IssueWriter
from taigun.db.lister import Lister
from taigun.db.milestone import MilestoneWriter
from taigun.db.project import ProjectCreator, ProjectExistsError, ProjectUpdater
from taigun.db.story import StoryWriter
from taigun.db.task import TaskWriter
from taigun.exceptions import (
    ConfigError,
    DatabaseConnectionError,
    IdentityChangeError,
    MilestoneConflictError,
    MilestoneMissingError,
    ProjectMissingError,
    ResolveError,
    TaigunError,
    TicketConflictError,
    TicketMissingError,
)
from taigun.parsers.file import FileParser
from taigun.parsers.frontmatter import FrontmatterParser
from taigun.resolver import Resolver
from taigun.state import StateFile, hash_file, locate_sidecar

_WRITERS = {
    "story": StoryWriter,
    "issue": IssueWriter,
    "task": TaskWriter,
    "epic": EpicWriter,
    "milestone": MilestoneWriter,
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
    except DatabaseConnectionError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    config.save(new_profile, name=None if profile == "default" else profile)
    typer.echo(f"Profile '{profile}' saved.")


@app.command()
def push(
    files: List[Path] = typer.Argument(..., help="Ticket file(s) to push."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Resolve FKs but do not insert."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
    force: bool = typer.Option(
        False, "--force",
        help="Skip conflict / missing-ticket prompts (overwrite / re-insert automatically)."
    ),
) -> None:
    """Parse and push (or update) one or more ticket files to Taiga.

    On non-dry-run pushes, the sidecar (``.taigun/state.yaml``) is located by
    walking up from the first source file's directory. All source files are
    expected to live in the same repo.

    Per ADR-004: if the sidecar has an entry for a source file, push dispatches
    to update; otherwise it inserts. Unchanged files (matching content hash)
    are a no-op. Modified-date drift and missing-in-Taiga cases prompt the user
    unless ``--force`` is set.
    """
    config = _load_config(profile)
    parser = FileParser()
    fm_parser = FrontmatterParser()
    manager = ConnectionManager(config)
    any_failed = False

    if files:
        sidecar_path = locate_sidecar(Path(files[0]).resolve().parent)
        state = StateFile(sidecar_path)
        state.load()
    else:
        state = None

    try:
        for path in files:
            try:
                ticket = parser.parse(path)
                ticket_type = type(ticket).__name__.lower()
                writer_class = _WRITERS[ticket_type]

                metadata, _ = fm_parser.parse(Path(path).read_text())
                metadata_keys = set(metadata.keys())

                entry = state.find(path) if state is not None else None

                if entry is None:
                    _handle_insert(
                        path, ticket, ticket_type, writer_class,
                        manager, config, state, dry_run,
                    )
                else:
                    _handle_upsert(
                        path, ticket, ticket_type, writer_class,
                        metadata_keys, entry, manager, config, state, force, dry_run,
                    )

            except TaigunError as e:
                typer.echo(f"✗ {Path(path).name}: {e}", err=True)
                any_failed = True
                continue
    finally:
        if state is not None and not dry_run:
            state.save()

    if any_failed:
        raise typer.Exit(code=1)


def _handle_insert(
    path: Path,
    ticket,
    ticket_type: str,
    writer_class,
    manager: ConnectionManager,
    config: Profile,
    state: Optional[StateFile],
    dry_run: bool,
) -> None:
    """Insert a new ticket and record it in the sidecar.

    On dry-run: resolve the project (validates it exists — cheap SELECT)
    and print the would-insert line. The actual INSERT is skipped so the
    per-project ref sequence is not advanced (E12 #57).
    """
    if dry_run:
        with manager.connect(dry_run=True) as conn:
            Resolver(conn).resolve_project(ticket.project)
        typer.echo(f"~ {ticket_type}: \"{ticket.subject}\"")
        return

    with manager.connect() as conn:
        resolver = Resolver(conn)
        writer = writer_class(conn, resolver)
        ref = writer.write(ticket, config.acting_user)

    if state is not None:
        state.record(
            path,
            project=ticket.project,
            ref=ref,
            ticket_type=ticket_type,
            content_hash=hash_file(path),
        )

    if ticket_type == "milestone":
        typer.echo(f"✓ {ticket_type}: \"{ticket.subject}\"")
    else:
        typer.echo(f"✓ #{ref} {ticket_type}: \"{ticket.subject}\"")


def _handle_upsert(
    path: Path,
    ticket,
    ticket_type: str,
    writer_class,
    metadata_keys: set,
    entry,
    manager: ConnectionManager,
    config: Profile,
    state: StateFile,
    force: bool,
    dry_run: bool = False,
) -> None:
    """Update an existing ticket (identified via the sidecar entry) or, on a
    missing-in-Taiga prompt confirmation, re-insert it.

    On dry-run: report what the real push would do based on the identity
    triple and content-hash comparison. Skips the writer.update() /
    writer.write() calls so no rows are touched (E12 #57). Missing-in-Taiga
    and conflict prompts are not surfaced in dry-run — those need a live
    DB round-trip and interactive confirmation that dry-run shouldn't do.
    """
    if entry.project != ticket.project:
        raise IdentityChangeError(
            f"project changed from '{entry.project}' to '{ticket.project}' — "
            f"remove the sidecar entry to push as a new ticket"
        )
    if entry.ticket_type != ticket_type:
        raise IdentityChangeError(
            f"type changed from '{entry.ticket_type}' to '{ticket_type}' — "
            f"remove the sidecar entry to push as a new ticket"
        )

    ref_label = "" if ticket_type == "milestone" else f"#{entry.ref} "

    current_hash = hash_file(path)
    if current_hash == entry.content_hash:
        prefix = "~ " if dry_run else ""
        typer.echo(f"{prefix}(unchanged) {ref_label}{ticket_type}: \"{ticket.subject}\"")
        return

    if dry_run:
        typer.echo(f"~ {ref_label}{ticket_type}: \"{ticket.subject}\" (would update)")
        return

    with manager.connect() as conn:
        resolver = Resolver(conn)
        writer = writer_class(conn, resolver)

        try:
            writer.update(
                ticket, entry.ref, metadata_keys,
                config.acting_user, entry.last_pushed_at,
            )

        except (TicketConflictError, MilestoneConflictError) as e:
            if not force and not typer.confirm(
                f"Taiga row for {ref_label}{ticket_type} was modified at "
                f"{e.taiga_modified_date} (after last push). Overwrite?",
                default=False,
            ):
                typer.echo(f"↷ {ref_label}{ticket_type}: skipped (Taiga was edited)")
                return

            writer.update(
                ticket, entry.ref, metadata_keys,
                config.acting_user, entry.last_pushed_at,
                ignore_conflict=True,
            )

        except (TicketMissingError, MilestoneMissingError) as e:
            if not force and not typer.confirm(
                f"{e}. Re-insert as new?",
                default=True,
            ):
                typer.echo(f"↷ {ticket_type}: skipped (not in Taiga, user declined re-insert)")
                return

            new_ref = writer.write(ticket, config.acting_user)
            new_ref_label = "" if ticket_type == "milestone" else f"#{new_ref} "

            state.record(
                path,
                project=ticket.project,
                ref=new_ref,
                ticket_type=ticket_type,
                content_hash=current_hash,
            )
            typer.echo(f"✓ {new_ref_label}{ticket_type}: \"{ticket.subject}\" (re-inserted)")
            return

    state.record(
        path,
        project=ticket.project,
        ref=entry.ref,
        ticket_type=ticket_type,
        content_hash=current_hash,
    )
    typer.echo(f"↺ {ref_label}{ticket_type}: \"{ticket.subject}\" (updated)")


@projects_app.command("create")
def projects_create(
    name: str = typer.Argument(..., help="Project name."),
    slug: str = typer.Argument(..., help="Project slug."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """Create a new Taiga project."""
    config = _load_config(profile)

    try:
        with ConnectionManager(config).connect() as conn:
            resolver = Resolver(conn)
            creator = ProjectCreator(conn, resolver)
            project_id, project_slug = creator.create(name, slug, config.acting_user)
    except (DatabaseConnectionError, ProjectExistsError, ResolveError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Created project #{project_id}: {project_slug}")


@projects_app.command("update")
def projects_update(
    slug: str = typer.Argument(..., help="Slug of the project to update."),
    name: Optional[str] = typer.Option(None, "--name", help="New project name."),
    description: Optional[str] = typer.Option(
        None, "--description",
        help="New project description (pass '' to clear).",
    ),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """Update an existing Taiga project's name and/or description."""
    if name is None and description is None:
        typer.echo("Nothing to update: pass --name and/or --description.", err=True)
        raise typer.Exit(code=1)

    config = _load_config(profile)

    try:
        with ConnectionManager(config).connect() as conn:
            updater = ProjectUpdater(conn)
            updater.update(slug, name=name, description=description)
    except (DatabaseConnectionError, ProjectMissingError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Updated project '{slug}'")


@projects_app.command("list")
def projects_list(
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List all projects on the configured instance."""
    config = _load_config(profile)

    try:
        with ConnectionManager(config).connect() as conn:
            lister = Lister(conn)
            projects = lister.list_projects()
    except DatabaseConnectionError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    for name, slug in projects:
        typer.echo(f"{name} ({slug})")


@epics_app.command("list")
def epics_list(
    project_slug: str = typer.Argument(..., help="Project slug."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List all epics in a project."""
    config = _load_config(profile)
    try:
        with ConnectionManager(config).connect() as conn:
            resolver = Resolver(conn)
            lister = Lister(conn)
            project_id = resolver.resolve_project(project_slug)
            epics = lister.list_epics(project_id)
    except (DatabaseConnectionError, ResolveError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    for ref, subject in epics:
        typer.echo(f"#{ref}  {subject}")


@statuses_app.command("list")
def statuses_list(
    project_slug: str = typer.Argument(..., help="Project slug."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile to use."),
) -> None:
    """List statuses grouped by ticket type for a project."""
    config = _load_config(profile)
    try:
        with ConnectionManager(config).connect() as conn:
            resolver = Resolver(conn)
            lister = Lister(conn)
            project_id = resolver.resolve_project(project_slug)
            statuses = lister.list_statuses(project_id)
    except (DatabaseConnectionError, ResolveError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    for ticket_type, status_list in statuses.items():
        typer.echo(f"{ticket_type}:")
        for name, is_closed in status_list:
            suffix = "  [closed]" if is_closed else ""
            typer.echo(f"  {name}{suffix}")


def _load_config(profile: Optional[str]) -> Profile:
    """Load a connection profile, translating ConfigError to a clean Exit(1)."""
    try:
        return ConfigManager().load(profile)
    except ConfigError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)


def _profile_exists(config: ConfigManager, profile: str) -> bool:
    try:
        config.load(None if profile == "default" else profile)
        return True
    except ConfigError:
        return False
