# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SparePart(models.Model):
    _name = 'spare.part'
    _description = 'ชิ้นส่วนอะไหล่'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char(
        string='ชื่ออะไหล่ (ไทย)', required=True, tracking=True)
    name_en = fields.Char(
        string='ชื่ออะไหล่ (อังกฤษ)', tracking=True)
    code = fields.Char(
        string='รหัสอะไหล่ (SKU)', required=True, copy=False,
        readonly=True, default=lambda self: _('New'), tracking=True)
    category_id = fields.Many2one(
        'spare.category', string='หมวดหมู่',
        required=True, tracking=True, index=True)
    
    # ข้อมูลรถ
    motorcycle_ids = fields.Many2many(
        'spare.motorcycle', string='รุ่นรถที่ใช้ได้',
        help='เลือกรุ่นรถที่สามารถใช้อะไหล่นี้ได้')
    brand = fields.Char(string='ยี่ห้อ', default='Honda')
    
    # ราคาและสต็อก
    price = fields.Float(string='ราคา (บาท)', digits=(12, 2), tracking=True)
    cost = fields.Float(string='ราคาทุน (บาท)', digits=(12, 2))
    qty_on_hand = fields.Float(
        string='จำนวนในสต็อก', compute='_compute_qty_on_hand',
        store=True, digits=(12, 2))
    min_qty = fields.Float(
        string='จำนวนขั้นต่ำ', default=5.0, digits=(12, 2),
        help='แจ้งเตือนเมื่อสต็อกต่ำกว่าจำนวนนี้')
    qty_reserved = fields.Float(
        string='จำนวนจอง', digits=(12, 2), default=0)
    
    # สถานะ
    stock_status = fields.Selection([
        ('in_stock', 'มีสต็อก'),
        ('low_stock', 'สต็อกต่ำ'),
        ('out_of_stock', 'หมดสต็อก'),
    ], string='สถานะสต็อก', compute='_compute_stock_status', store=True)
    
    # คุณภาพ
    part_type = fields.Selection([
        ('oem', 'OEM'),
        ('aftermarket', 'Aftermarket'),
    ], string='OEM/Aftermarket', default='oem', tracking=True)
    quality_brand = fields.Char(string='คุณภาพ/แบรนด์')
    warranty_months = fields.Integer(string='ชุดประกัน (เดือน)', default=0)
    
    # อื่นๆ
    image = fields.Binary(string='รูปภาพ', attachment=True)
    note = fields.Text(string='หมายเหตุ')
    active = fields.Boolean(default=True, string='เปิดใช้งาน')
    
    # การเคลื่อนย้าย
    stock_move_ids = fields.One2many(
        'spare.stock.move', 'part_id', string='ประวัติการเคลื่อนย้าย')
    move_count = fields.Integer(
        string='จำนวนการเคลื่อนย้าย', compute='_compute_move_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                # สร้าง prefix ตามหมวดหมู่
                category = self.env['spare.category'].browse(vals.get('category_id'))
                prefix_map = {
                    'เครื่องยนต์': 'ENG',
                    'กรอง/น้ำมัน': 'FLT',
                    'ระบบเบรก': 'BRK',
                    'ระบบส่งกำลัง': 'TRN',
                    'ระบบไฟฟ้า': 'ELC',
                    'ช่วงล่าง': 'SUS',
                    'ยาง/ล้อ': 'WHL',
                    'ตัวถัง/พลาสติก': 'BDY',
                    'ระบบเชื้อเพลิง': 'FUL',
                    'ท่อไอเสีย': 'EXH',
                    'น้ำมัน/สารหล่อลื่น': 'OIL',
                    'สายควบคุม': 'CBL',
                }
                prefix = prefix_map.get(category.name, 'SPR') if category else 'SPR'
                seq = self.env['ir.sequence'].next_by_code('spare.part') or '0001'
                vals['code'] = '%s-%s' % (prefix, seq)
        return super().create(vals_list)

    @api.depends('stock_move_ids', 'stock_move_ids.qty', 'stock_move_ids.move_type', 'stock_move_ids.state')
    def _compute_qty_on_hand(self):
        for part in self:
            moves = part.stock_move_ids.filtered(lambda m: m.state == 'done')
            qty_in = sum(moves.filtered(lambda m: m.move_type == 'in').mapped('qty'))
            qty_out = sum(moves.filtered(lambda m: m.move_type == 'out').mapped('qty'))
            part.qty_on_hand = qty_in - qty_out

    @api.depends('qty_on_hand', 'min_qty')
    def _compute_stock_status(self):
        for part in self:
            if part.qty_on_hand <= 0:
                part.stock_status = 'out_of_stock'
            elif part.qty_on_hand <= part.min_qty:
                part.stock_status = 'low_stock'
            else:
                part.stock_status = 'in_stock'

    @api.depends('stock_move_ids')
    def _compute_move_count(self):
        for part in self:
            part.move_count = len(part.stock_move_ids)

    def action_view_moves(self):
        """แสดงประวัติการเคลื่อนย้าย"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'ประวัติการเคลื่อนย้าย - %s' % self.name,
            'res_model': 'spare.stock.move',
            'view_mode': 'tree,form',
            'domain': [('part_id', '=', self.id)],
            'context': {'default_part_id': self.id},
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
         'รหัสอะไหล่นี้มีอยู่แล้ว!'),
    ]
