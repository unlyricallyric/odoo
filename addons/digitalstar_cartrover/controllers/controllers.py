# -*- coding: utf-8 -*-
from odoo import http

# class MyModule(http.Controller):
#     @http.route('/digitalstar_cartrover/digitalstar_cartrover/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/digitalstar_cartrover/digitalstar_cartrover/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('digitalstar_cartrover.listing', {
#             'root': '/digitalstar_cartrover/digitalstar_cartrover',
#             'objects': http.request.env['digitalstar_cartrover.digitalstar_cartrover'].search([]),
#         })

#     @http.route('/digitalstar_cartrover/digitalstar_cartrover/objects/<model("digitalstar_cartrover.digitalstar_cartrover"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('digitalstar_cartrover.object', {
#             'object': obj
#         })