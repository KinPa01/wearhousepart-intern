# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SpareWarehouse(models.Model):
    _name = 'spare.warehouse'
    _description = 'คลังสินค้า'
    _order = 'code'

    name = fields.Char(string='ชื่อคลัง', required=True)
    code = fields.Char(string='รหัสคลัง', required=True, size=10)
    address = fields.Text(string='ที่อยู่')
    manager_id = fields.Many2one(
        'res.users', string='ผู้จัดการคลัง')
    location_ids = fields.One2many(
        'spare.location', 'warehouse_id', string='ตำแหน่งจัดเก็บ')
    location_count = fields.Integer(
        string='จำนวนตำแหน่ง', compute='_compute_location_count')
    active = fields.Boolean(default=True, string='เปิดใช้งาน')
    note = fields.Text(string='หมายเหตุ')

    @api.depends('location_ids')
    def _compute_location_count(self):
        for wh in self:
            wh.location_count = len(wh.location_ids)

    def action_view_locations(self):
        """แสดงตำแหน่งจัดเก็บทั้งหมดในคลัง"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'ตำแหน่ง - %s' % self.name,
            'res_model': 'spare.location',
            'view_mode': 'tree,form',
            'domain': [('warehouse_id', '=', self.id)],
            'context': {'default_warehouse_id': self.id},
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'รหัสคลังนี้มีอยู่แล้ว!'),
    ]
