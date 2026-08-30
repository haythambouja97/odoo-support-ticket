# from odoo import http


# class SupportTicket(http.Controller):
#     @http.route('/support_ticket/support_ticket', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/support_ticket/support_ticket/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('support_ticket.listing', {
#             'root': '/support_ticket/support_ticket',
#             'objects': http.request.env['support_ticket.support_ticket'].search([]),
#         })

#     @http.route('/support_ticket/support_ticket/objects/<model("support_ticket.support_ticket"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('support_ticket.object', {
#             'object': obj
#         })

