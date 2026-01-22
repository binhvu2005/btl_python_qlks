from odoo import fields, models


class EduClassroom(models.Model):
    _name = "edu.classroom"
    _description = "Education Classroom"

    name = fields.Char(required=True)
    capacity = fields.Integer(string="Sức chứa", default=0)
