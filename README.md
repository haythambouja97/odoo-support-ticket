# Support Ticket Management

An Odoo 19 app for tracking customer support tickets. One model, `support.ticket`,
with auto-generated references, a customer and assignee, priority, and a four-step
status workflow. Internal users get list, form, kanban and search views under a Support
menu; customers get a portal where they can submit tickets and follow them.

Depends on `base`, `mail` and `portal`.

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
- Chatter on every ticket — message log, followers and scheduled activities, via
  `mail.thread` and `mail.activity.mixin`
- Customer portal: a ticket list at `/my/tickets`, a detail page with chatter, and a
  submission form, plus a card on the portal home with a ticket count
- Access rights for internal users, and a separate portal ACL and record rule scoping
  customers to their own tickets
- Archiving via the standard `active` flag

## Architecture

```
support_ticket/
├── __manifest__.py            # metadata, dependencies, data file load order
├── __init__.py
├── models/
│   ├── __init__.py
│   └── models.py              # the support.ticket model
├── controllers/
│   ├── __init__.py
│   └── portal.py              # the /my/tickets routes
├── security/
│   ├── ir.model.access.csv    # CRUD grants, internal and portal
│   └── security.xml           # record rule scoping portal users to their own tickets
├── data/
│   └── ir_sequence.xml        # seeds the sequence for ticket references
└── views/
    ├── views.xml              # action, backend views, menus
    └── portal_templates.xml   # QWeb templates for the portal pages
```

`__manifest__.py` is what makes this a module — Odoo scans the addons paths for
directories containing one. The `data` key is a load order, not a set, so the ACL
file goes first.

`security/ir.model.access.csv` isn't optional. Odoo denies access by default, so a
model with no ACL row is unreachable for everyone except the superuser. The filename
has to match the model it loads into, so don't rename it.

`security/security.xml` holds the portal record rule. ACLs decide which models you can
touch; record rules decide which rows. Portal access needs both.

`controllers/portal.py` is the only part of the module that isn't declarative. It
subclasses `CustomerPortal` from the `portal` addon, which is what makes the pages
inherit the portal layout, breadcrumbs and home page.

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
free. I decided against it, mostly because of the coupling: tickets would inherit
Project's own views, reports and menus, and every customisation anyone made to tasks
later would land on tickets too.

The vocabulary doesn't really fit either. Tasks have a `project_id`, planned hours and
timesheets; tickets need a customer, a priority and a small fixed set of statuses. You
end up carrying fields that never apply or quietly repurposing ones that mean something
else.

The module did end up depending on `mail` and `portal` for the chatter and the customer
pages, so it isn't as dependency-free as I first intended. Those two are deliberate and
narrow, though — `mail` and `portal` are infrastructure that most apps build on, whereas
`project` would have brought a whole application's data model with it.

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

### Customer portal

I originally scoped the portal out and asked whether it was expected. The answer was
yes — customers should be able to submit and follow their own tickets from the website —
so it went in.

It's three routes on a controller inheriting `CustomerPortal`: a list at `/my/tickets`, a
detail page with the chatter on it, and a submission form. There's also an override of
`_prepare_home_portal_values` so the ticket count shows on the portal home card.

Security is two layers, because ACLs and record rules answer different questions. The ACL
grants `base.group_portal` read and create but not write or delete, which decides what a
portal user can do to the model at all. The record rule
`[('customer_id', '=', user.partner_id.id)]` decides which rows they see, so a customer
only ever gets their own tickets — the `search([])` in the list route looks unscoped but
isn't, because the rule is applied underneath it. The detail route also calls
`check_access('read')` explicitly, so guessing another ticket's id in the URL raises
rather than leaking anything.

On submission, `customer_id` comes from `request.env.user.partner_id`, never from the
form, so a customer can't open a ticket in someone else's name.

The one thing worth explaining is the `sudo()` on create. It isn't there to dodge the
ACL — it's there because the `create` override calls `next_by_code`, and read access to
`ir.sequence` is granted to internal users only. Without `sudo()` a portal submission
fails on the sequence lookup rather than on the ticket itself. Forcing `customer_id` from
the session is what keeps that safe.

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

**A portal route that 404'd because I'd dropped the `@`.** I wrote the first portal
route, restarted, and `/my/tickets` returned a 404. The module had installed cleanly, the
template was there, the controller file was being imported — nothing anywhere said
anything was wrong. I'd written `http.route(...)` without the `@`, so instead of
decorating the function it just called `http.route` and threw the result away, leaving an
ordinary method that Odoo had no reason to map to a URL. The pattern is the same one as
the `group_expand` problem: valid Python that does nothing, and no error to lead you to
it. Now when something doesn't appear at all — a route, a menu, a kanban column — my
first assumption is that the code never registered, not that it registered wrongly.

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
