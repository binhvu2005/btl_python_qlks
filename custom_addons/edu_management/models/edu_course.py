from odoo import api, fields, models, _


class EduSubject(models.Model):
    _name = "edu.subject"
    _description = "Education Subject"

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    course_ids = fields.One2many("edu.course", "subject_id", string="Khóa học")

    _sql_constraints = [
        ("subject_code_unique", "unique(code)", "Mã chuyên ngành phải là duy nhất.")
    ]


class EduCourse(models.Model):
    _name = "edu.course"
    _description = "Education Course"

    name = fields.Char(required=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    level = fields.Selection(
        [("basic", "Cơ bản"), ("advanced", "Nâng cao")],
        default="basic",
    )
    responsible_id = fields.Many2one("res.users", string="Người phụ trách")
    subject_id = fields.Many2one("edu.subject", string="Chuyên ngành")
    session_ids = fields.One2many("edu.session", "course_id", string="Lớp học")
    session_count = fields.Integer(compute="_compute_session_count", string="Số lớp học")

    _sql_constraints = [
        ("course_name_unique", "unique(name)", "Tên khóa học phải là duy nhất.")
    ]

    @api.depends("session_ids")
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.session_ids)

    @api.onchange("responsible_id")
    def _onchange_responsible_id(self):
        for record in self:
            if (
                record.responsible_id
                and record.responsible_id.email
                and not record.description
            ):
                record.description = _("Email phụ trách: %s") % record.responsible_id.email
