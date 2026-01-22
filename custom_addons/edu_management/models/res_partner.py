from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_instructor = fields.Boolean(string="Là giảng viên")
    session_teaching_ids = fields.One2many(
        "edu.session", "instructor_id", string="Lớp đang dạy"
    )
    session_teaching_count = fields.Integer(
        compute="_compute_session_teaching_count", string="Số lớp đang dạy"
    )
    session_attending_ids = fields.Many2many(
        "edu.session",
        string="Lớp đang học",
        relation="edu_session_partner_rel",
        column1="partner_id",
        column2="session_id",
    )

    @api.depends("session_teaching_ids")
    def _compute_session_teaching_count(self):
        for record in self:
            record.session_teaching_count = len(record.session_teaching_ids)
