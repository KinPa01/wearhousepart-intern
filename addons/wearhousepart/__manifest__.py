# -*- coding: utf-8 -*-
{
    'name': 'คลังอะไหล่ - Warehouse Part',
    'version': '17.0.1.0.0',
    'summary': 'ระบบจัดการคลังอะไหล่มอเตอร์ไซค์',
    'description': """
        ระบบจัดการคลังอะไหล่มอเตอร์ไซค์
        =================================
        - จัดการหมวดหมู่อะไหล่
        - จัดการชิ้นส่วนอะไหล่ (SKU, ราคา, สต็อก)
        - บันทึกการเคลื่อนย้ายสต็อก (รับเข้า/เบิกออก)
        - แจ้งเตือนสต็อกต่ำ
        - รองรับรุ่นรถ Honda
    """,
    'author': 'Warehouse Part Team',
    'website': '',
    'category': 'Inventory',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/spare_category_data.xml',
        'data/spare_motorcycle_data.xml',
        'views/spare_category_views.xml',
        'views/spare_part_views.xml',
        'views/spare_stock_move_views.xml',
        'views/spare_motorcycle_views.xml',
        'views/spare_dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/spare_part_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wearhousepart/static/src/css/wearhousepart.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
}
