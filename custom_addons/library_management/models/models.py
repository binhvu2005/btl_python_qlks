# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta


class LibraryCategory(models.Model):
    _name = 'library.category'
    _description = 'Thể loại sách'

    name = fields.Char(string='Tên thể loại', required=True)


class LibraryAuthor(models.Model):
    _name = 'library.author'
    _description = 'Tác giả'

    name = fields.Char(string='Tên tác giả', required=True)
    bio = fields.Text(string='Tiểu sử')


class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Lịch sử mượn'

    borrower_name = fields.Char(string='Tên người mượn')
    borrow_date = fields.Date(string='Ngày mượn', default=fields.Date.context_today)
    return_date = fields.Date(string='Ngày trả')
    is_returned = fields.Boolean(string='Đã trả', default=False)
    book_id = fields.Many2one('library.book', string='Sách', ondelete='cascade')

    duration = fields.Integer(string='Số ngày mượn', compute='_compute_duration', store=True)

    @api.depends('borrow_date', 'return_date')
    def _compute_duration(self):
        for rec in self:
            if rec.borrow_date and rec.return_date:
                bd = fields.Date.from_string(rec.borrow_date)
                rd = fields.Date.from_string(rec.return_date)
                rec.duration = (rd - bd).days
            else:
                rec.duration = 0

    @api.onchange('borrow_date')
    def _onchange_borrow_date(self):
        for rec in self:
            if rec.borrow_date:
                bd = fields.Date.from_string(rec.borrow_date)
                rec.return_date = (bd + timedelta(days=7)).isoformat()


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Sách trong thư viện'

    name = fields.Char(string='Tên sách', required=True)
    isbn = fields.Char(string='Mã ISBN')
    state = fields.Selection([
        ('draft', 'Mới nhập'),
        ('available', 'Có sẵn'),
        ('borrowed', 'Đang mượn'),
        ('lost', 'Đã mất')
    ], string='Trạng thái', default='draft')

    condition = fields.Selection([
        ('0', 'Kém'),
        ('1', 'TB'),
        ('2', 'Tốt'),
        ('3', 'Mới')
    ], string='Tình trạng', default='2')

    purchase_price = fields.Integer(string='Giá nhập sách')
    category_id = fields.Many2one('library.category', string='Thể loại')
    author_ids = fields.Many2many('library.author', string='Tác giả')
    loan_ids = fields.One2many('library.loan', 'book_id', string='Lịch sử mượn trả')

    short_description = fields.Char(string='Mô tả ngắn', compute='_compute_short_description', store=True)
    purchase_date = fields.Date(string='Ngày nhập sách', default=fields.Date.context_today)
    days_since_purchase = fields.Integer(string='Tuổi đời sách (ngày)', compute='_compute_days_since_purchase', store=True)
    total_loans = fields.Integer(string='Tổng số lần mượn', compute='_compute_total_loans', store=True)
    notes = fields.Text(string='Ghi chú')

    # helper integer field to display condition as stars
    condition_level = fields.Integer(compute='_compute_condition_level')

    @api.depends('name', 'author_ids', 'isbn')
    def _compute_short_description(self):
        for rec in self:
            authors = ', '.join(rec.author_ids.mapped('name')) if rec.author_ids else 'Unknown'
            rec.short_description = f"{rec.name} - {authors} ({rec.isbn or ''})"

    @api.depends('purchase_date')
    def _compute_days_since_purchase(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        for rec in self:
            if rec.purchase_date:
                pd = fields.Date.from_string(rec.purchase_date)
                rec.days_since_purchase = (today - pd).days
            else:
                rec.days_since_purchase = 0

    @api.depends('loan_ids')
    def _compute_total_loans(self):
        for rec in self:
            rec.total_loans = len(rec.loan_ids) if rec.loan_ids else 0

    @api.depends('condition')
    def _compute_condition_level(self):
        mapping = {'0': 1, '1': 2, '2': 3, '3': 4}
        for rec in self:
            rec.condition_level = mapping.get(rec.condition, 0)

    @api.onchange('state')
    def _onchange_state(self):
        for rec in self:
            if rec.state == 'lost':
                rec.condition = '0'

    @api.onchange('isbn')
    def _onchange_isbn(self):
        for rec in self:
            if rec.isbn and len(rec.isbn) > 13:
                return {
                    'warning': {
                        'title': 'Cảnh báo',
                        'message': 'Mã ISBN không chuẩn (thường tối đa 13 số)'
                    }
                }

    @api.onchange('category_id')
    def _onchange_category(self):
        for rec in self:
            if rec.category_id:
                rec.notes = f"Sách thuộc thể loại {rec.category_id.name} - Vui lòng xếp đúng kệ."
