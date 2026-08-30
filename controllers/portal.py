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
    
    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth='user', website=True)
    def portal_ticket_detail(self, ticket_id, **kw):
        ticket = request.env['support.ticket'].browse(ticket_id)
        ticket.check_access('read')
        return request.render('support_ticket.portal_ticket_detail', {
            'ticket': ticket,
            'page_name': 'ticket',
        })

    @http.route(['/my/tickets/new'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_ticket_new(self, **post):
        if request.httprequest.method == 'POST':
            ticket = request.env['support.ticket'].sudo().create({
                'title': post.get('title'),
                'description': post.get('description'),
                'customer_id': request.env.user.partner_id.id,
                'priority': post.get('priority', '1'),
            })
            return request.redirect('/my/tickets/%s' % ticket.id)

        return request.render('support_ticket.portal_ticket_new', {
            'page_name': 'ticket',
        })