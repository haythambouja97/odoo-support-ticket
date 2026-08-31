# Support Ticket Management
 
An Odoo 19 module for customer support tickets.
 
Internal users manage tickets from the backend — list, form, kanban and search
views under a Support menu. Customers submit and follow their own tickets from
the portal, and get an email when the status changes.
 
Depends on `base`, `mail` and `portal`.
 
## Approach
 
I had never used Odoo before this. I started by getting an empty module to
install, to confirm the environment worked, then built in verifiable steps — the
model, then access rights, then views, then the menu — installing after each one
to see what broke. The commit history follows that progression.
 
Where the documentation wasn't enough, I read Odoo's own addons. Most tutorials
online target versions 14 to 17, and several things they teach no longer work in
19; that's where most of the research time went (see Difficulties).
 
The portal came later. I had deliberately left it out of scope, asked whether it
was expected, and the answer was yes — so it was added, along with email
notifications.
 
## Installation
 
Odoo 19.0, Python 3.11, PostgreSQL 16.
 
Put `support_ticket/` in a folder listed in `addons_path`:
 
```ini
addons_path = /path/to/odoo/addons,/path/to/custom_addons
```
 
Point at the folder *containing* `support_ticket`, not at `support_ticket`
itself.
 
```bash
# install
python odoo-bin -c odoo.conf -d <database> -i support_ticket
 
# apply later changes
python odoo-bin -c odoo.conf -d <database> -u support_ticket
```
 
## Features
 
**Backend**
- Tickets with title, description, customer, assignee and priority
- Automatic references (`TKT00001`) from an `ir.sequence`
- Status workflow: New → In Progress → Resolved → Closed
- Kanban grouped by status with drag-and-drop; all columns show even when empty
- Search filters and grouping by status, priority or customer
- Chatter with message history and followers
**Portal**
- Ticket list at `/my/tickets`
- Detail page with a message thread the customer can reply to
- Submission form
- Email notification to the customer when the status changes
## Files
 
```
support_ticket/
├── __manifest__.py
├── models/models.py           the support.ticket model
├── controllers/portal.py      the /my/tickets routes
├── security/
│   ├── ir.model.access.csv    who can access the model
│   └── security.xml           which rows portal users can see
├── data/
│   ├── ir_sequence.xml        ticket reference numbering
│   └── mail_template.xml      status change notification
└── views/
    ├── views.xml              backend views and menus
    └── portal_templates.xml   portal pages
```
 
Two notes on how Odoo works, since both surprised me coming from other
frameworks:
 
**Views are database records.** The XML in `views/` doesn't render anything —
each `<record>` creates a row in `ir_ui_view`. That's what lets another module
extend this form without editing the file: it declares its own view with
`inherit_id` pointing here, and Odoo merges them at request time.
 
**There are no migrations.** Odoo derives the schema from the Python classes and
syncs it on every `-u`. Adding a field means editing `models.py` and re-running
the upgrade.
 
## Design decisions
 
**A standalone model, not an extension of `project.task`.** Inheriting would have
given me stages, assignment and a kanban board for free, but it makes `project` a
hard dependency and tickets would appear inside Project's own views and reports.
The vocabulary doesn't fit either — tasks have planned hours and timesheets where
a ticket needs a customer and a fixed status set. The cost is that everything
Project would have provided has to be built by hand, and I haven't built all of
it.
 
**`Selection` fields for priority and status.** Both are fixed vocabulary,
not data users should edit at runtime, so adding a status is a code change. If
configurable stages were ever needed the answer would be a
`support.ticket.stage` model, not a longer `Selection`.
 
**`ondelete="restrict"` on the customer, `"set null"` on the assignee.** A ticket
without a customer is meaningless, so deleting a partner who has tickets is
blocked. The assignee is metadata about handling, so deleting a user just leaves
their tickets unassigned.
 
**Portal security is two layers.** The ACL grants `base.group_portal` read and
create but not write or delete — that decides what they can do to the model. A
record rule `[('customer_id', '=', user.partner_id.id)]` decides which rows they
see. The `search([])` in the controller looks unscoped but isn't; the ORM applies
the rule underneath. The detail route also calls `check_access('read')`, so
guessing a ticket id in the URL fails rather than leaking anything. On
submission, `customer_id` comes from the session, never the form.
 
**Email covers outgoing only.** Status changes notify the customer through
`mail.thread` and a mail template. Incoming mail — customers creating or
replying to tickets by email — would need a mail alias and gateway, which is
configuration beyond a local dev setup.
 
## Difficulties
 
**`<group expand="0" string="Group By">` broke the search view.** Every example I
found wraps group-by filters in that element, so I did too, and the module
wouldn't install. The exception only said the search view was invalid. The useful
information was above the traceback: RelaxNG validation warnings naming the
rejected attributes. Removing the wrapper fixed it, and the filters still land in
the Group By menu because Odoo sorts them by the `group_by` key in their context,
not by nesting.
 
**`group_expand` did nothing in the kanban.** Only the "New" column showed, so
there was nowhere to drag a card. I'd written `group_expand` as an attribute in
the kanban view, which is how older examples do it, and got no error — just no
columns. It's a Python argument on the field definition now.
 
**A portal route that 404'd because I dropped the `@`.** I'd written
`http.route(...)` without the decorator syntax, so it called the function and
discarded the result, leaving a method Odoo never mapped to a URL. Nothing
reported a problem. Same shape as the `group_expand` issue: valid Python that
does nothing.
 
**Menus missing because the file never parsed.** I added the `<menuitem>`
records, ran `-u`, and the menu wasn't there. I checked the parent, the action,
group restrictions, the browser cache — all fine. The menu items had ended up
after the closing `</odoo>` tag, so the file was invalid XML. Data files load in
a transaction, so the whole load rolled back and the module silently stayed on
its previous version.
 
**The "New Ticket" button was hidden from customers who had none.** I'd put the
link inside the `t-if="tickets"` block, so a new customer — the person most
likely to need it — couldn't see it. I only found this after logging in as a real
portal user instead of testing as admin, which also made me verify the record
rule properly. Admin bypasses record rules entirely, so nothing I'd tested up to
that point had proven the portal security worked.
 
## Licence
 
LGPL-3
 