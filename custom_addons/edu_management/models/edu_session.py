from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EduSession(models.Model):
    _name = "edu.session"
    _description = "Education Session"
    _order = "start_date desc, name"

    name = fields.Char(required=True)
    code = fields.Char(readonly=True, default="New")
    state = fields.Selection(
        [
            ("draft", "Dự thảo"),
            ("open", "Mở đăng ký"),
            ("done", "Kết thúc"),
            ("cancel", "Hủy"),
        ],
        default="draft",
        string="Trạng thái",
    )
    start_date = fields.Date(string="Ngày bắt đầu")
    duration = fields.Float(string="Thời lượng (ngày)", default=1.0)
    end_date = fields.Date(compute="_compute_end_date", store=True, string="Ngày kết thúc")
    seats = fields.Integer(string="Số ghế", compute="_compute_seats", store=True, readonly=False)
    taken_seats = fields.Float(
        compute="_compute_taken_seats", string="Tỷ lệ lấp đầy (%)", store=True
    )
    product_id = fields.Many2one(
        "product.template",
        string="Học phí",
        domain=[("is_edu_fee", "=", True)],
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        string="Tiền tệ",
    )
    revenue = fields.Monetary(
        compute="_compute_revenue", string="Doanh thu dự kiến", store=True
    )
    course_id = fields.Many2one("edu.course", string="Khóa học", required=True)
    instructor_id = fields.Many2one(
        "res.partner",
        string="Giảng viên",
        domain=[("is_instructor", "=", True)],
    )
    classroom_id = fields.Many2one("edu.classroom", string="Phòng học")
    attendee_ids = fields.Many2many(
        "res.partner",
        string="Học viên",
        relation="edu_session_partner_rel",
        column1="session_id",
        column2="partner_id",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Tự động điền start_date là ngày mai
        tomorrow = fields.Date.today() + timedelta(days=1)
        if "start_date" in fields_list:
            res["start_date"] = tomorrow
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "New") == "New":
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("edu.session") or "New"
                )
        return super().create(vals_list)

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code and record.code != "New":
                name = f"[{record.code}] {name}"
            if record.start_date:
                name = f"{name} - {record.start_date}"
            result.append((record.id, name))
        return result

    def copy(self, default=None):
        default = default or {}
        default.update({
            "state": "draft",
            "attendee_ids": [(5, 0, 0)],  # Xóa danh sách học viên
            "code": "New",
        })
        return super().copy(default)

    @api.depends("classroom_id.capacity")
    def _compute_seats(self):
        for record in self:
            record.seats = record.classroom_id.capacity if record.classroom_id else 0

    @api.depends("start_date", "duration")
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.duration:
                record.end_date = fields.Date.to_date(record.start_date) + relativedelta(
                    days=int(record.duration)
                )
            else:
                record.end_date = False

    @api.depends("attendee_ids", "seats")
    def _compute_taken_seats(self):
        for record in self:
            seats = record.seats or 0
            record.taken_seats = (
                len(record.attendee_ids) / seats * 100 if seats else 0.0
            )

    @api.depends("attendee_ids", "product_id.list_price")
    def _compute_revenue(self):
        for record in self:
            price = record.product_id.list_price if record.product_id else 0.0
            record.revenue = price * len(record.attendee_ids)

    @api.onchange("course_id")
    def _onchange_course_id(self):
        """Tự động điền giảng viên từ responsible_id của khóa học"""
        if self.course_id and self.course_id.responsible_id:
            # Tìm partner tương ứng với user
            partner = self.env["res.partner"].search([
                ("user_ids", "in", self.course_id.responsible_id.id)
            ], limit=1)
            if not partner:
                # Nếu không tìm thấy, tìm partner có email giống user
                partner = self.env["res.partner"].search([
                    ("email", "=", self.course_id.responsible_id.email)
                ], limit=1)
            if partner and partner.is_instructor:
                self.instructor_id = partner

    @api.onchange("seats")
    def _onchange_seats(self):
        """Validate số ghế không được âm"""
        if self.seats and self.seats < 0:
            return {
                "warning": {
                    "title": _("Cảnh báo"),
                    "message": _("Số ghế không được âm. Đã tự động đặt về 0."),
                }
            }
        if self.seats and self.seats < 0:
            self.seats = 0

    @api.constrains("instructor_id", "attendee_ids")
    def _check_instructor_not_attendee(self):
        """Giảng viên không được có trong danh sách học viên"""
        for record in self:
            if record.instructor_id and record.instructor_id in record.attendee_ids:
                raise ValidationError(
                    _("Giảng viên phụ trách không được có tên trong danh sách học viên của lớp này.")
                )

    @api.constrains("duration", "start_date")
    def _check_duration_and_start_date(self):
        """Thời lượng phải > 0 và ngày bắt đầu không được để trống"""
        for record in self:
            if record.duration and record.duration <= 0:
                raise ValidationError(_("Thời lượng khóa học phải lớn hơn 0."))
            if not record.start_date:
                raise ValidationError(_("Ngày bắt đầu không được để trống."))

    def action_open(self):
        """Chuyển state từ Draft -> Open (Mở đăng ký)"""
        for record in self:
            if not record.classroom_id:
                raise UserError(_("Phải chọn phòng học trước khi mở đăng ký."))
            if not record.instructor_id:
                raise UserError(_("Phải chọn giảng viên trước khi mở đăng ký."))
            record.state = "open"
        return True

    def action_done(self):
        """Chuyển state từ Open -> Done (Kết thúc)"""
        for record in self:
            record.state = "done"
        return True

    def action_cancel(self):
        """Chuyển state -> Cancel (Hủy)"""
        for record in self:
            if record.state == "done":
                raise UserError(_("Không thể hủy lớp học đã kết thúc."))
            record.state = "cancel"
        return True

    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Cho phép tìm kiếm bằng mã lớp hoặc tên giảng viên"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("code", operator, name),
                ("instructor_id.name", operator, name),
            ]
        return self.search(domain + args, limit=limit).name_get()

    def unlink(self):
        """Chỉ cho phép xóa lớp ở trạng thái Draft hoặc Cancel"""
        for record in self:
            if record.state not in ("draft", "cancel"):
                raise UserError(
                    _("Chỉ có thể xóa lớp học ở trạng thái 'Dự thảo' hoặc 'Hủy'.")
                )
        return super().unlink()
