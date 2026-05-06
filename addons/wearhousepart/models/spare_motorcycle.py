# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SpareMotorcycle(models.Model):
    _name = 'spare.motorcycle'
    _description = 'รุ่นมอเตอร์ไซค์'
    _order = 'name'

    name = fields.Char(string='รุ่นรถ', required=True)
    image_1920 = fields.Image(string='รูปภาพ', max_width=1920, max_height=1920)
    model_type = fields.Selection([
        ('classic_cub', 'Classic Cub'),
        ('classic_commuter', 'Classic Commuter'),
        ('sport', 'Sport'),
        ('commuter', 'Commuter'),
        ('naked_sport', 'Naked Sport'),
        ('automatic_scooter', 'Automatic Scooter'),
        ('premium_scooter', 'Premium Scooter'),
        ('adventure_scooter', 'Adventure Scooter'),
        ('maxi_scooter', 'Maxi Scooter'),
        ('adventure', 'Adventure'),
    ], string='ประเภท')
    engine_cc = fields.Integer(string='ขนาดเครื่อง (cc)')
    transmission = fields.Char(string='ระบบส่งกำลัง')
    msrp_price = fields.Float(string='ราคา MSRP (บาท)', digits=(12, 2))
    production_year = fields.Char(string='ยุคการผลิต')
    production_status = fields.Selection([
        ('discontinued', 'ยุติการผลิต'),
        ('current', 'ผลิตอยู่'),
        ('discontinued_thai', 'ยุติการผลิต (ไทย)'),
    ], string='สถานะการผลิต')
    active = fields.Boolean(default=True, string='เปิดใช้งาน')
    
    part_ids = fields.Many2many(
        'spare.part', string='อะไหล่ที่ใช้ได้')
    part_count = fields.Integer(
        string='จำนวนอะไหล่', compute='_compute_part_count')

    @api.depends('part_ids')
    def _compute_part_count(self):
        for moto in self:
            moto.part_count = len(moto.part_ids)

    def action_view_parts(self):
        """แสดงอะไหล่ที่ใช้ได้กับรุ่นรถนี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'อะไหล่ - %s' % self.name,
            'res_model': 'spare.part',
            'view_mode': 'tree,kanban,form',
            'domain': [('motorcycle_ids', 'in', self.id)],
            'context': {},
        }
