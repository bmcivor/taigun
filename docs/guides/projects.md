# Managing projects

Tickets can only be pushed into a project that already exists. taigun can list,
create, and update projects on the configured instance; all three commands accept
`--profile`.

## Listing projects

```
$ taigun projects list
My Project (my-project-slug)
Another Project (another-slug)
```

The value in parentheses is the **slug** — the identifier ticket files use in
their `project:` frontmatter field.

## Creating a project

```
$ taigun projects create "My Project" my-project-slug
Created project #1: my-project-slug
```

The new project is built from the instance's default project template, the same
way Taiga itself does it:

- Statuses for every ticket type, plus priorities, severities, issue types, and
  point scales, copied from the template
- The template's default status/priority/severity selections wired up
- A fresh ref sequence (ticket numbering starts at `#1`)
- The acting user as owner, with an admin membership

Epics, backlog, kanban, wiki, and issues modules are all enabled, and the project
is created **public** (`is_private` off) — flip that in the Taiga UI if you need a
private project.

Creating a project whose slug already exists is an error, not an upsert.

## Updating a project

Renaming or re-describing an existing project is flag-driven — no source file or
sidecar involved:

```
$ taigun projects update my-project-slug --name "Better Name"
Updated project 'my-project-slug'

$ taigun projects update my-project-slug --description "What this project is for"
Updated project 'my-project-slug'
```

Only the flags you pass are written. To clear the description, pass an empty
string (`--description ''`). Name and description are the only fields the command
exposes — taigun offers no way to change a slug.
