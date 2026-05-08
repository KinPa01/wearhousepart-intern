# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SparePurchaseOrder(models.Model):
    _name = 'spare.purchase.order'
    _description = 'ใบสั่งซื้ออะไหล่'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'

    name = fields.Char(
        string='เลขที่ PO', required=True, copy=False,
        readonly=True, default=lambda self: _('New'))
    supplier = fields.Char(
        string='ผู้จำหน่าย', required=True, tracking=True)
    supplier_ref = fields.Char(string='เลขอ้างอิงผู้จำหน่าย')
    date_order = fields.Date(
        string='วันที่สั่งซื้อ', default=fields.Date.context_today,
        required=True, tracking=True)
    date_planned = fields.Date(
        string='วันที่คาดว่าจะได้รับ', tracking=True)
    date_received = fields.Date(
        string='วันที่ได้รับจริง', readonly=True)
    warehouse_id = fields.Many2one(
        'spare.warehouse', string='คลังปลายทาง',
        required=True, tracking=True)
    line_ids = fields.One2many(
        'spare.purchase.order.line', 'order_id',
        string='รายการสั่งซื้อ')
    state = fields.Selection([
        ('draft', 'ร่าง'),
        ('confirmed', 'ยืนยันแล้ว'),
        ('received', 'รับของแล้ว'),
        ('done', 'จัดเก็บแล้ว'),
        ('cancel', 'ยกเลิก'),
    ], string='สถานะ', default='draft', tracking=True, index=True)
    user_id = fields.Many2one(
        'res.users', string='ผู้จัดซื้อ',
        default=lambda self: self.env.user, tracking=True)
    total_amount = fields.Float(
        string='ยอดรวม (บาท)', compute='_compute_total_amount',
        store=True, digits=(12, 2))
    line_count = fields.Integer(
        string='จำนวนรายการ', compute='_compute_line_count')
    note = fields.Text(string='หมายเหตุ')
    priority = fields.Selection([
        ('0', 'ปกติ'),
        ('1', 'ด่วน'),
        ('2', 'ด่วนมาก'),
    ], string='ความสำคัญ', default='0')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'spare.purchase.order') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(order.line_ids.mapped('subtotal'))

    @api.depends('line_ids')
    def _compute_line_count(self):
        for order in self:
            order.line_count = len(order.line_ids)

    def action_view_lines(self):
        """เปิดรายการสั่งซื้อของ PO นี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'รายการสั่งซื้อ',
            'res_model': 'spare.purchase.order.line',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_confirm(self):
        """ยืนยัน PO"""
        for order in self:
            if order.state != 'draft':
                raise UserError(
                    'สามารถยืนยันได้เฉพาะ PO สถานะร่างเท่านั้น')
            if not order.line_ids:
                raise UserError(
                    'กรุณาเพิ่มรายการสั่งซื้ออย่างน้อย 1 รายการ')
            order.state = 'confirmed'

    def action_receive(self):
        """รับของ → สร้าง stock move IN"""
        for order in self:
            if order.state != 'confirmed':
                raise UserError(
                    'สามารถรับของได้เฉพาะ PO ที่ยืนยันแล้วเท่านั้น')
            for line in order.line_ids:
                self.env['spare.stock.move'].create({
                    'part_id': line.part_id.id,
                    'qty': line.qty,
                    'move_type': 'in',
                    'reference': order.name,
                    'note': 'รับของจาก PO: %s / %s' % (
                        order.name, order.supplier),
                    'purchase_order_id': order.id,
                })
            order.date_received = fields.Date.context_today(self)
            order.state = 'received'

    def action_putaway(self):
        """จัดเก็บ Putaway → ยืนยัน stock move + อัพเดท location"""
        for order in self:
            if order.state != 'received':
                raise UserError(
                    'สามารถจัดเก็บได้เฉพาะ PO ที่รับของแล้วเท่านั้น')
            moves = self.env['spare.stock.move'].search([
                ('purchase_order_id', '=', order.id),
                ('state', '=', 'draft'),
            ])
            for move in moves:
                move.action_confirm()
            for line in order.line_ids:
                if line.dest_location_id:
                    line.part_id.location_id = line.dest_location_id.id
            order.state = 'done'

    def action_cancel(self):
        """ยกเลิก PO"""
        for order in self:
            if order.state == 'done':
                raise UserError(
                    'ไม่สามารถยกเลิก PO ที่จัดเก็บแล้วได้')
            moves = self.env['spare.stock.move'].search([
                ('purchase_order_id', '=', order.id),
                ('state', '=', 'draft'),
            ])
            for move in moves:
                move.action_cancel()
            order.state = 'cancel'

    def action_draft(self):
        """กลับเป็นร่าง"""
        for order in self:
            if order.state == 'cancel':
                order.state = 'draft'


class SparePurchaseOrderLine(models.Model):
    _name = 'spare.purchase.order.line'
    _description = 'รายการสั่งซื้ออะไหล่'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'spare.purchase.order', string='ใบสั่งซื้อ',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='ลำดับ', default=10)
    part_id = fields.Many2one(
        'spare.part', string='อะไหล่', required=True)
    category_id = fields.Many2one(
        related='part_id.category_id', string='หมวดหมู่',
        store=True, readonly=True)
    qty = fields.Float(
        string='จำนวนสั่งซื้อ', required=True,
        digits=(12, 2), default=1)
    price_unit = fields.Float(
        string='ราคาต่อหน่วย', digits=(12, 2))
    subtotal = fields.Float(
        string='ยอดรวม', compute='_compute_subtotal',
        store=True, digits=(12, 2))
    dest_location_id = fields.Many2one(
        'spare.location', string='ตำแหน่งจัดเก็บ (Putaway)',
        help='ตำแหน่งที่จะนำอะไหล่ไปจัดเก็บ')
    state = fields.Selection(
        related='order_id.state', string='สถานะ', store=True)

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit

    @api.onchange('part_id')
    def _onchange_part_id(self):
        if self.part_id:
            self.price_unit = self.part_id.cost or self.part_id.price
            if self.part_id.location_id:
                self.dest_location_id = self.part_id.location_id
