from odoo import api, fields, models

class SupportTicket(models.Model):

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('support.ticket') or 'New'
        return super().create(vals_list)

    _name = "support.ticket"
    _description = "Customer Support Ticket"
    _order = "create_date desc"

    name = fields.Char(
        string="Ticket Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )

    title = fields.Char(
        string="Title",
        required=True,
    )

    description = fields.Text(
        string="Description",
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        ondelete="restrict",
    )

    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        ondelete="set null",
    )

    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Urgent"),
        ],
        string="Priority",
        default="1",
        required=True,
    )

    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="new",
        required=True,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

