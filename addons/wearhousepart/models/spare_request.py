# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SpareRequest(models.Model):
    _name = 'spare.request'
    _description = 'ใบขอเบิกอะไหล่'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc, id desc'

    name = fields.Char(
        string='เลขที่ใบเบิก', required=True, copy=False,
        readonly=True, default=lambda self: _('New'))
    requester_id = fields.Many2one(
        'res.users', string='ผู้ขอเบิก',
        default=lambda self: self.env.user,
        required=True, tracking=True)
    approver_id = fields.Many2one(
        'res.users', string='ผู้อนุมัติ', tracking=True)
    department = fields.Char(
        string='แผนก/ฝ่าย', tracking=True)
    date_request = fields.Date(
        string='วันที่ขอเบิก', default=fields.Date.context_today,
        required=True, tracking=True)
    date_approved = fields.Date(
        string='วันที่อนุมัติ', readonly=True)
    date_done = fields.Date(
        string='วันที่เบิกจริง', readonly=True)
    line_ids = fields.One2many(
        'spare.request.line', 'request_id',
        string='รายการเบิก')
    state = fields.Selection([
        ('draft', 'ร่าง'),
        ('submitted', 'รออนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ไม่อนุมัติ'),
        ('picking', 'กำลังหยิบของ'),
        ('done', 'เสร็จสิ้น'),
        ('cancel', 'ยกเลิก'),
    ], string='สถานะ', default='draft', tracking=True, index=True)
    reason = fields.Text(string='เหตุผลการเบิก')
    reject_reason = fields.Text(string='เหตุผลที่ไม่อนุมัติ')
    note = fields.Text(string='หมายเหตุ')
    priority = fields.Selection([
        ('0', 'ปกติ'),
        ('1', 'ด่วน'),
        ('2', 'ด่วนมาก'),
    ], string='ความสำคัญ', default='0')
    line_count = fields.Integer(
        string='จำนวนรายการ', compute='_compute_line_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'spare.request') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for req in self:
            req.line_count = len(req.line_ids)

    def action_submit(self):
        """ส่งขออนุมัติ"""
        for req in self:
            if req.state != 'draft':
                raise UserError(
                    'สามารถส่งขออนุมัติได้เฉพาะสถานะร่างเท่านั้น')
            if not req.line_ids:
                raise UserError(
                    'กรุณาเพิ่มรายการเบิกอย่างน้อย 1 รายการ')
            req.state = 'submitted'

    def action_approve(self):
        """หัวหน้าอนุมัติ"""
        for req in self:
            if req.state != 'submitted':
                raise UserError(
                    'สามารถอนุมัติได้เฉพาะใบเบิกที่รออนุมัติเท่านั้น')
            for line in req.line_ids:
                if not line.qty_approved:
                    line.qty_approved = line.qty_requested
            req.approver_id = self.env.user
            req.date_approved = fields.Date.context_today(self)
            req.state = 'approved'

    def action_reject(self):
        """หัวหน้าปฏิเสธ"""
        for req in self:
            if req.state != 'submitted':
                raise UserError(
                    'สามารถปฏิเสธได้เฉพาะใบเบิกที่รออนุมัติเท่านั้น')
            req.approver_id = self.env.user
            req.state = 'rejected'

    def action_pick(self):
        """หยิบของ → สร้าง stock move OUT"""
        for req in self:
            if req.state != 'approved':
                raise UserError(
                    'สามารถหยิบของได้เฉพาะใบเบิกที่อนุมัติแล้วเท่านั้น')
            for line in req.line_ids:
                qty = line.qty_approved or line.qty_requested
                if qty > line.part_id.qty_on_hand:
                    raise UserError(
                        'อะไหล่ "%s" สต็อกไม่พอ! '
                        '(ต้องการ %s, คงเหลือ %s)' % (
                            line.part_id.name, qty,
                            line.part_id.qty_on_hand))
            for line in req.line_ids:
                qty = line.qty_approved or line.qty_requested
                if qty > 0:
                    self.env['spare.stock.move'].create({
                        'part_id': line.part_id.id,
                        'qty': qty,
                        'move_type': 'out',
                        'reference': req.name,
                        'note': 'เบิกตามใบขอเบิก: %s (%s)' % (
                            req.name, req.reason or ''),
                        'request_id': req.id,
                    })
            req.state = 'picking'

    def action_done(self):
        """ยืนยันหยิบของเสร็จ → confirm stock moves"""
        for req in self:
            if req.state != 'picking':
                raise UserError(
                    'สามารถยืนยันได้เฉพาะใบเบิกที่กำลังหยิบของเท่านั้น')
            moves = self.env['spare.stock.move'].search([
                ('request_id', '=', req.id),
                ('state', '=', 'draft'),
            ])
            for move in moves:
                move.action_confirm()
            req.date_done = fields.Date.context_today(self)
            req.state = 'done'

    def action_cancel(self):
        """ยกเลิกใบเบิก"""
        for req in self:
            if req.state == 'done':
                raise UserError(
                    'ไม่สามารถยกเลิกใบเบิกที่เสร็จแล้วได้')
            moves = self.env['spare.stock.move'].search([
                ('request_id', '=', req.id),
                ('state', '=', 'draft'),
            ])
            for move in moves:
                move.action_cancel()
            req.state = 'cancel'

    def action_draft(self):
        """กลับเป็นร่าง"""
        for req in self:
            if req.state in ('cancel', 'rejected'):
                req.state = 'draft'


class SpareRequestLine(models.Model):
    _name = 'spare.request.line'
    _description = 'รายการเบิกอะไหล่'
    _order = 'sequence, id'

    request_id = fields.Many2one(
        'spare.request', string='ใบเบิก',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='ลำดับ', default=10)
    part_id = fields.Many2one(
        'spare.part', string='อะไหล่', required=True)
    category_id = fields.Many2one(
        related='part_id.category_id', string='หมวดหมู่',
        store=True, readonly=True)
    qty_requested = fields.Float(
        string='จำนวนที่ขอ', required=True,
        digits=(12, 2), default=1)
    qty_approved = fields.Float(
        string='จำนวนที่อนุมัติ', digits=(12, 2))
    qty_on_hand = fields.Float(
        related='part_id.qty_on_hand',
        string='สต็อกคงเหลือ', readonly=True)
    src_location_id = fields.Many2one(
        'spare.location', string='หยิบจากตำแหน่ง',
        help='ตำแหน่งที่จะไปหยิบอะไหล่')
    state = fields.Selection(
        related='request_id.state', string='สถานะ', store=True)

    @api.onchange('part_id')
    def _onchange_part_id(self):
        if self.part_id and self.part_id.location_id:
            self.src_location_id = self.part_id.location_id
