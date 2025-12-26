# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError


# SATELLITE MODELS
class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Loại phòng'

    name = fields.Char(string='Tên loại phòng', required=True)
    code = fields.Char(string='Mã loại')


class HotelService(models.Model):
    _name = 'hotel.service'
    _description = 'Dịch vụ đi kèm'

    name = fields.Char(string='Tên dịch vụ', required=True)
    price = fields.Integer(string='Giá dịch vụ', default=0)

    _sql_constraints = [
        ('price_positive', 'CHECK (price > 0)', 'Giá dịch vụ phải lớn hơn 0'),
    ]


class HotelCustomer(models.Model):
    _name = 'hotel.customer'
    _description = 'Khách hàng'

    name = fields.Char(string='Tên khách hàng', required=True)
    identity_card = fields.Char(string='Số CMND/CCCD')
    phone = fields.Char(string='Số điện thoại')

    _sql_constraints = [
        ('identity_card_unique', 'UNIQUE (identity_card)', 'Số CMND/CCCD phải duy nhất'),
    ]


# MAIN MODELS
class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Phòng khách sạn'

    name = fields.Char(string='Số phòng', required=True)
    floor = fields.Integer(string='Tầng')
    price_per_night = fields.Integer(string='Giá thuê 1 đêm', default=0)
    status = fields.Selection([
        ('available', 'Trống'),
        ('occupied', 'Đang ở'),
        ('maintenance', 'Bảo trì')
    ], string='Trạng thái', default='available')

    type_id = fields.Many2one('hotel.room.type', string='Loại phòng')

    _sql_constraints = [
        ('name_unique', 'UNIQUE (name)', 'Số phòng phải duy nhất'),
        ('price_positive', 'CHECK (price_per_night > 0)', 'Giá phòng phải lớn hơn 0'),
    ]


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Phiếu đặt phòng'

    code = fields.Char(string='Mã booking', required=True)
    check_in = fields.Date(string='Ngày nhận phòng', default=fields.Date.context_today)
    check_out = fields.Date(string='Ngày trả phòng')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành')
    ], string='Trạng thái', default='draft')

    customer_id = fields.Many2one('hotel.customer', string='Khách hàng', required=True)
    room_id = fields.Many2one('hotel.room', string='Phòng', required=True)
    service_ids = fields.Many2many('hotel.service', string='Dịch vụ')

    duration = fields.Integer(string='Số đêm lưu trú', compute='_compute_duration', store=True)
    total_amount = fields.Integer(string='Tổng thành tiền', compute='_compute_total_amount', store=True)

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                ci = fields.Date.from_string(rec.check_in)
                co = fields.Date.from_string(rec.check_out)
                rec.duration = (co - ci).days
            else:
                rec.duration = 0

    @api.depends('duration', 'room_id', 'service_ids')
    def _compute_total_amount(self):
        for rec in self:
            room_price = (rec.room_id.price_per_night or 0) * (rec.duration or 0)
            service_price = sum(rec.service_ids.mapped('price')) if rec.service_ids else 0
            rec.total_amount = room_price + service_price

    @api.onchange('room_id')
    def _onchange_room_id(self):
        for rec in self:
            if rec.room_id and rec.room_id.status == 'maintenance':
                return {
                    'warning': {
                        'title': 'Cảnh báo',
                        'message': 'Phòng này đang bảo trì, vui lòng chọn phòng khác!'
                    }
                }

    @api.onchange('check_in')
    def _onchange_check_in(self):
        for rec in self:
            if rec.check_in:
                ci = fields.Date.from_string(rec.check_in)
                rec.check_out = (ci + timedelta(days=1)).isoformat()

    @api.constrains('check_out', 'check_in')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                ci = fields.Date.from_string(rec.check_in)
                co = fields.Date.from_string(rec.check_out)
                if co <= ci:
                    raise ValidationError('Ngày trả phòng không hợp lệ!')

    @api.constrains('room_id')
    def _check_room_occupied(self):
        for rec in self:
            if rec.room_id and rec.room_id.status == 'occupied':
                raise ValidationError('Phòng này đang có khách ở!')
