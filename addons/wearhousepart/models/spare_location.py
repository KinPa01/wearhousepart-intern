# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SpareLocation(models.Model):
    _name = 'spare.location'
    _description = 'ตำแหน่งจัดเก็บ'
    _order = 'complete_code'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_code'

    name = fields.Char(string='ชื่อตำแหน่ง', required=True)
    code = fields.Char(string='รหัส', required=True)
    complete_code = fields.Char(
        string='รหัสเต็ม', compute='_compute_complete_code',
        store=True, recursive=True)
    warehouse_id = fields.Many2one(
        'spare.warehouse', string='คลัง', required=True, index=True)
    parent_id = fields.Many2one(
        'spare.location', string='ตำแหน่งหลัก',
        index=True, ondelete='cascade')
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'spare.location', 'parent_id', string='ตำแหน่งย่อย')
    location_type = fields.Selection([
        ('zone', 'โซน (Zone)'),
        ('row', 'แถว (Row)'),
        ('shelf', 'ชั้นวาง (Shelf)'),
        ('bin', 'ช่อง (Bin)'),
        ('receiving', 'จุดรับของ (Receiving)'),
        ('shipping', 'จุดจัดส่ง (Shipping)'),
    ], string='ประเภทตำแหน่ง', required=True, default='shelf')
    category_id = fields.Many2one(
        'spare.category', string='หมวดหมู่ที่แนะนำ',
        help='หมวดหมู่อะไหล่ที่แนะนำให้จัดเก็บที่ตำแหน่งนี้')
    capacity = fields.Integer(string='ความจุ (ชิ้น)', default=100)
    part_ids = fields.One2many(
        'spare.part', 'location_id', string='อะไหล่ที่จัดเก็บ')
    part_count = fields.Integer(
        string='จำนวนอะไหล่', compute='_compute_part_count')
    active = fields.Boolean(default=True, string='เปิดใช้งาน')
    color = fields.Integer(string='สี')
    barcode = fields.Char(string='บาร์โค้ด', copy=False)
    note = fields.Text(string='หมายเหตุ')

    @api.depends('code', 'parent_id.complete_code', 'warehouse_id.code')
    def _compute_complete_code(self):
        for loc in self:
            if loc.parent_id:
                loc.complete_code = '%s-%s' % (
                    loc.parent_id.complete_code, loc.code)
            elif loc.warehouse_id:
                loc.complete_code = '%s-%s' % (
                    loc.warehouse_id.code, loc.code)
            else:
                loc.complete_code = loc.code

    @api.depends('part_ids')
    def _compute_part_count(self):
        for loc in self:
            loc.part_count = len(loc.part_ids)

    def action_view_parts(self):
        """แสดงอะไหล่ที่จัดเก็บที่ตำแหน่งนี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'อะไหล่ใน %s' % self.complete_code,
            'res_model': 'spare.part',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    _sql_constraints = [
        ('barcode_uniq', 'unique (barcode)',
         'บาร์โค้ดนี้มีอยู่แล้ว!'),
    ]
