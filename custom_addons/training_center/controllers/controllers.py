# -*- coding: utf-8 -*-
# from odoo import http


# class TrainingCenter(http.Controller):
#     @http.route('/training_center/training_center', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/training_center/training_center/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('training_center.listing', {
#             'root': '/training_center/training_center',
#             'objects': http.request.env['training_center.training_center'].search([]),
#         })

#     @http.route('/training_center/training_center/objects/<model("training_center.training_center"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('training_center.object', {
#             'object': obj
#         })

