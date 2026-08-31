{
    'name': "Support Ticket Management",

    'summary': "Manage customer support tickets through their lifecycle",

    'description': """
Support Ticket Management
=========================

Create, assign, prioritize and track customer support tickets.

Features:
- Ticket creation linked to customers (res.partner)
- Assignment to internal users
- Priority and type classification
- Status workflow from reception to closure
- Search, filter and group tickets
    """,

    'author': "Haytham Boujelben",
    'website': "https://github.com/haythambouja97/odoo-support-ticket",

    'category': 'Services/Helpdesk',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'application': True,
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'portal'],

    # always loaded, order matters
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/mail_template.xml',
        'security/security.xml',
        'views/views.xml',
        'views/portal_templates.xml',
    ],
}