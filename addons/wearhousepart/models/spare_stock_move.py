# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SpareStockMove(models.Model):
    _name = 'spare.stock.move'
    _description = 'การเคลื่อนย้ายสต็อกอะไหล่'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='เลขที่เอกสาร', required=True, copy=False,
        readonly=True, default=lambda self: _('New'))
    part_id = fields.Many2one(
        'spare.part', string='อะไหล่', required=True,
        tracking=True, index=True)
    category_id = fields.Many2one(
        related='part_id.category_id', string='หมวดหมู่',
        store=True, readonly=True)
    qty = fields.Float(
        string='จำนวน', required=True, digits=(12, 2),
        tracking=True)
    move_type = fields.Selection([
        ('in', 'รับเข้า'),
        ('out', 'เบิกออก'),
    ], string='ประเภท', required=True, default='in', tracking=True)
    state = fields.Selection([
        ('draft', 'ร่าง'),
        ('done', 'เสร็จสิ้น'),
        ('cancel', 'ยกเลิก'),
    ], string='สถานะ', default='draft', tracking=True)
    date = fields.Datetime(
        string='วันที่', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        'res.users', string='ผู้ดำเนินการ',
        default=lambda self: self.env.user, tracking=True)
    reference = fields.Char(string='อ้างอิง')
    note = fields.Text(string='หมายเหตุ')

    # ข้อมูลเพิ่มเติม
    qty_before = fields.Float(
        string='จำนวนก่อน', digits=(12, 2), readonly=True)
    qty_after = fields.Float(
        string='จำนวนหลัง', digits=(12, 2), readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                move_type = vals.get('move_type', 'in')
                if move_type == 'in':
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'spare.stock.move.in') or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'spare.stock.move.out') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        """ยืนยันการเคลื่อนย้าย"""
        for move in self:
            if move.state != 'draft':
                raise UserError('สามารถยืนยันได้เฉพาะเอกสารที่อยู่ในสถานะร่างเท่านั้น')
            if move.qty <= 0:
                raise ValidationError('จำนวนต้องมากกว่า 0')
            
            # บันทึกจำนวนก่อน
            move.qty_before = move.part_id.qty_on_hand
            
            # ตรวจสอบกรณีเบิกออก
            if move.move_type == 'out':
                if move.qty > move.part_id.qty_on_hand:
                    raise UserError(
                        'จำนวนเบิก (%s) มากกว่าสต็อกคงเหลือ (%s)' % (
                            move.qty, move.part_id.qty_on_hand))
            
            move.state = 'done'
            
            # บันทึกจำนวนหลัง (qty_on_hand จะ recompute อัตโนมัติ)
            move.qty_after = move.part_id.qty_on_hand
            
            # ตรวจสอบสต็อกต่ำ
            if move.part_id.qty_on_hand <= move.part_id.min_qty:
                move._notify_low_stock()

    def action_cancel(self):
        """ยกเลิกการเคลื่อนย้าย"""
        for move in self:
            if move.state == 'done':
                raise UserError('ไม่สามารถยกเลิกเอกสารที่ยืนยันแล้วได้')
            move.state = 'cancel'

    def action_draft(self):
        """กลับเป็นร่าง"""
        for move in self:
            if move.state == 'cancel':
                move.state = 'draft'

    def _notify_low_stock(self):
        """แจ้งเตือนสต็อกต่ำ"""
        self.ensure_one()
        if self.part_id.qty_on_hand <= self.part_id.min_qty:
            # ส่งข้อความแจ้งเตือนผ่าน chatter
            self.part_id.message_post(
                body='⚠️ แจ้งเตือน: สต็อกต่ำ! อะไหล่ "%s" เหลือ %s ชิ้น (ขั้นต่ำ: %s ชิ้น)' % (
                    self.part_id.name,
                    self.part_id.qty_on_hand,
                    self.part_id.min_qty),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
