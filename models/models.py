# from odoo import models, fields, api


# class support_ticket(models.Model):
#     _name = 'support_ticket.support_ticket'
#     _description = 'support_ticket.support_ticket'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

