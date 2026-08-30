# Support Ticket Management

An Odoo 19 app for tracking customer support tickets. One model, `support.ticket`,
with auto-generated references, a customer and assignee, priority, and a four-step
status workflow. List, form, kanban and search views under a Support menu.

Only depends on `base`, so it installs on a bare database without pulling in CRM or
Project.

## Installation

Built and tested on Odoo 19.0 with Python 3.11 and PostgreSQL 16.

Put the module in a directory on your addons path:

```
support-ticket-management/
├── odoo19/          # Odoo source
└── custom_addons/
    └── support_ticket/
```

Add that directory to `addons_path` in `odoo.conf`:

```ini
[options]
addons_path = /path/to/odoo19/addons,/path/to/custom_addons
db_host = localhost
db_port = 5432
db_user = odoo
db_password = <your-password>
admin_passwd = <your-master-password>
http_port = 8069
```

Point at the folder *containing* `support_ticket`, not at `support_ticket` itself. I
got this wrong the first time and spent a while wondering why the module never showed
up in the Apps list.

Install:

```bash
python odoo-bin -c odoo.conf -d support_ticket_management -i support_ticket
```

Use `-u` instead of `-i` to pick up code changes afterwards:

```bash
python odoo-bin -c odoo.conf -d support_ticket_management -u support_ticket
```

If it doesn't show up under Apps, click *Update Apps List* — Odoo only rescans the
addons paths when asked.

## Features

- Ticket creation with title, description and customer
- Automatic reference numbering (`TKT00001`, from a Postgres sequence)
- Assignment to an internal user
- Four priority levels, shown as stars
- Status workflow: New → In Progress → Resolved → Closed, with buttons on the form
- Kanban board grouped by status, drag-and-drop between columns, all columns visible
  even when empty
- Search filters (by status, "My Tickets") and grouping by status, priority or customer
- Access rights for internal users
- Archiving via the standard `active` flag

## Architecture

```
support_ticket/
├── __manifest__.py            # metadata, dependencies, data file load order
├── __init__.py
├── models/
│   ├── __init__.py
│   └── models.py              # the support.ticket model
├── security/
│   └── ir.model.access.csv    # CRUD grants
├── data/
│   └── ir_sequence.xml        # seeds the sequence for ticket references
└── views/
    └── views.xml              # action, views, menus
```

`__manifest__.py` is what makes this a module — Odoo scans the addons paths for
directories containing one. The `data` key is a load order, not a set, so the ACL
file goes first.

`security/ir.model.access.csv` isn't optional. Odoo denies access by default, so a
model with no ACL row is unreachable for everyone except the superuser. The filename
has to match the model it loads into, so don't rename it.

`data/ir_sequence.xml` is marked `noupdate="1"` so upgrades don't reset the counter
and start handing out references that already exist.

### Views are records, not templates

The XML in `views/views.xml` doesn't render anything. Each `<record>` creates a row in
`ir_ui_view`, and the file just seeds those rows at install and re-syncs them on `-u`.

The point of that is extensibility: another module can add a field to this form
without touching this file, by creating its own `ir.ui.view` with `inherit_id` pointing
here and an `<xpath>` describing the change. Odoo merges them at request time. You
can't do that with a template file you don't own.

It also means views are validated when they're written, so a typo in a field name
fails the install rather than breaking a page for whoever opens it first.

### No migration files

There's no `migrations/` folder because Odoo derives the schema from the Python
classes on every install and upgrade. `-u support_ticket` rebuilds the registry, diffs
each field against the live table, and runs the `ALTER TABLE` statements itself. Add a
field to `models.py`, restart with `-u`, and the column is there.

Worth knowing: Odoo adds and widens columns but won't drop anything, so removing a
field from Python leaves the column behind.

## Design decisions

### Standalone model instead of inheriting `project.task`

Inheriting `project.task` would have given me stages, assignment and a kanban board for
free. I decided against it, mostly because of the coupling — it makes `project` a hard
dependency, which pulls in `mail`, `analytic` and `resource` with their menus, and
tickets would then appear inside Project's own views and reports.

The vocabulary doesn't really fit either. Tasks have a `project_id`, planned hours and
timesheets; tickets need a customer, a priority and a small fixed set of statuses. You
end up carrying fields that never apply or quietly repurposing ones that mean something
else.

The cost is that everything Project would have given me has to be built by hand, and I
haven't built all of it yet.

### `Selection` fields for priority and status

Both are stored as `varchar` with the allowed values enforced by the ORM, rather than
foreign keys to config tables.

Priority and status are fixed vocabulary here — decisions about how the process works,
not data users should edit at runtime. As `Selection` fields, adding a status is a code
change and a review, which feels like the right amount of friction for something the
business logic branches on. It's also simpler: no extra table, no menu, no access
rules, and domains stay readable.

The trade-off is that nobody can add a status without a developer. If configurable
stages ever became a real requirement, the answer would be a proper
`support.ticket.stage` model with `sequence` and `fold` fields, not a longer
`Selection`.

### `ondelete="restrict"` on customer, `"set null"` on assignee

Deleting a partner who has tickets is blocked. The customer is what the ticket is
*about*, so a ticket without one isn't degraded, it's meaningless — and `cascade` would
be worse, wiping a customer's whole support history at exactly the moment you'd want it.

Deleting a user just clears the assignee and leaves the tickets in place. Who's handling
a ticket is metadata, so losing it costs a reassignment rather than the record.

Both of these happen to be the ORM's defaults for required and optional many2one fields,
so neither line changes behaviour. I left them in so the intent is visible at the field
rather than inferred from whether `required` is set.

### No customer portal

No portal access, no `/my/tickets`, no website form, nothing for `base.group_portal` in
the ACL. Internal users only.

Portal access isn't one feature — it's a portal ACL plus record rules scoping customers
strictly to their own tickets, a controller and templates, token access for people
without a login, a submission form, and email notifications. Most of it is
security-critical, and one bad record rule means customer A reads customer B's tickets.

Leaving it out kept this to one model, one ACL and four views with the internal workflow
working properly. Nothing here blocks adding it later: `customer_id` already points at
`res.partner`, which is what portal users attach to.

## Difficulties encountered

**`<group expand="0" string="Group By">` broke the search view.** Every example I'd seen
wraps the group-by filters in that element, so I did too, and the module refused to
install. The exception itself only said the search view definition was invalid and named
the file, which wasn't much to go on — but scrolling up in the terminal there were
RelaxNG validation warnings above the traceback naming the specific attributes it had
rejected. Removing the wrapper and leaving the three filters directly under `<search>`
fixed it, and they still show up in the Group By menu, because Odoo sorts filters into
that menu based on the `group_by` key in their `context` rather than on how they're
nested. The lesson that stuck was to read the log above the traceback, not just the
error.

**`group_expand` did nothing in the kanban view.** An empty database only showed a "New"
column, so there was nowhere to drag a card to. I'd put `group_expand` on the field
inside the kanban arch, which is how the older examples do it, and got no error at all —
just no extra columns, which took longer to work out than an exception would have. It
turns out to be a Python argument on the field definition now, not a view attribute. I
added `_group_expand_states` on the model, which returns every key from the `state`
selection, and pointed the field at it with
`group_expand="_group_expand_states"`. All four columns render now, empty or not.

**Menus that were missing because the file never parsed.** I added the two `<menuitem>`
records, ran `-u`, the server started normally, and the Support menu wasn't there. I
checked the obvious things first — the `parent`, the action reference, whether a group
was hiding it, the browser cache — and they were all fine. The actual problem was that
the menu items had ended up *after* the closing `</odoo>` tag, so the file was invalid
XML and never parsed. Data files load in a transaction, so the whole load rolled back and
the module quietly stayed on its previous version; nothing looked broken from the outside
because the old views still worked. What I took from it is that a *missing* menu is
almost never a menu problem — a menu that loaded but was configured wrong turns up in the
wrong place or errors when you click it, whereas absence means the file didn't load at
all. I run `-u` in the foreground now so I can actually see the traceback.

## Licence

LGPL-3
