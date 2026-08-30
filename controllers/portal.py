from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class SupportTicketPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            values['ticket_count'] = request.env['support.ticket'].search_count([])
        return values

    @http.route(['/my/tickets'], type='http', auth='user', website=True)
    def portal_my_tickets(self, **kw):
        tickets = request.env['support.ticket'].search([])
        return request.render('support_ticket.portal_my_tickets', {
            'tickets': tickets,
            'page_name': 'ticket',
        })