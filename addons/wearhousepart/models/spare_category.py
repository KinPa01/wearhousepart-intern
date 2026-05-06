# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SpareCategory(models.Model):
    _name = 'spare.category'
    _description = 'หมวดหมู่อะไหล่'
    _order = 'name'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'

    name = fields.Char(string='ชื่อหมวดหมู่', required=True, translate=True)
    complete_name = fields.Char(
        string='ชื่อเต็ม', compute='_compute_complete_name',
        recursive=True, store=True)
    parent_id = fields.Many2one(
        'spare.category', string='หมวดหมู่หลัก',
        index=True, ondelete='cascade')
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'spare.category', 'parent_id', string='หมวดหมู่ย่อย')
    part_ids = fields.One2many(
        'spare.part', 'category_id', string='อะไหล่ในหมวดหมู่')
    part_count = fields.Integer(
        string='จำนวนอะไหล่', compute='_compute_part_count', store=True)
    color = fields.Integer(string='สี')
    icon = fields.Char(string='ไอคอน')
    active = fields.Boolean(default=True, string='เปิดใช้งาน')
    note = fields.Text(string='หมายเหตุ')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (
                    category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.depends('part_ids')
    def _compute_part_count(self):
        for category in self:
            category.part_count = len(category.part_ids)

    def action_view_parts(self):
        """แสดงอะไหล่ในหมวดหมู่"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'อะไหล่ - %s' % self.name,
            'res_model': 'spare.part',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }

    _sql_constraints = [
        ('name_uniq', 'unique (name, parent_id)',
         'ชื่อหมวดหมู่นี้มีอยู่แล้ว!'),
    ]
