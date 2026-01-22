from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_edu_fee = fields.Boolean(string="Là học phí", help="Đánh dấu sản phẩm là học phí.")
