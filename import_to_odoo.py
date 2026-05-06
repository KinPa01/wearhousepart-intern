# -*- coding: utf-8 -*-
"""Import ข้อมูลอะไหล่และ stock move เข้า Odoo ผ่าน XML-RPC"""
import xmlrpc.client
import random
from datetime import datetime, timedelta

# ====== ตั้งค่า Odoo Connection ======
URL = "http://localhost:8044"
DB = "wearhousepart"
USERNAME = "admin"
PASSWORD = "admin"

def connect():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        raise Exception("❌ เชื่อมต่อ Odoo ไม่สำเร็จ! ตรวจสอบ URL/DB/USERNAME/PASSWORD")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    print(f"✅ เชื่อมต่อ Odoo สำเร็จ (uid={uid})")
    return uid, models

def get_category_map(uid, models):
    cats = models.execute_kw(DB, uid, PASSWORD, 'spare.category', 'search_read', [[]], {'fields': ['id', 'name']})
    return {c['name']: c['id'] for c in cats}

def get_motorcycle_map(uid, models):
    motos = models.execute_kw(DB, uid, PASSWORD, 'spare.motorcycle', 'search_read', [[]], {'fields': ['id', 'name']})
    return {m['name']: m['id'] for m in motos}

def import_parts(uid, models):
    cat_map = get_category_map(uid, models)
    moto_map = get_motorcycle_map(uid, models)
    
    print(f"\n📦 หมวดหมู่ที่พบ: {list(cat_map.keys())}")
    print(f"🏍️ รุ่นรถที่พบ: {len(moto_map)} รุ่น")

    parts = [
        {"name": "ลูกสูบ", "name_en": "Piston", "cat": "เครื่องยนต์", "motos": "Wave 110i,Wave 125i", "price": 850, "cost": 550, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "แหวนลูกสูบ", "name_en": "Piston Ring", "cat": "เครื่องยนต์", "motos": "Wave 110i,Wave 125i", "price": 350, "cost": 220, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ประเก็นฝาสูบ", "name_en": "Head Gasket", "cat": "เครื่องยนต์", "motos": "Click 125i,Click 150i", "price": 180, "cost": 100, "min": 3, "type": "aftermarket", "brand": "NPP"},
        {"name": "วาล์วไอดี", "name_en": "Intake Valve", "cat": "เครื่องยนต์", "motos": "Wave 125i", "price": 280, "cost": 180, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "วาล์วไอเสีย", "name_en": "Exhaust Valve", "cat": "เครื่องยนต์", "motos": "Wave 125i", "price": 280, "cost": 180, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ก้านสูบ", "name_en": "Connecting Rod", "cat": "เครื่องยนต์", "motos": "Wave 110i", "price": 650, "cost": 420, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ปะเก็นครัช", "name_en": "Clutch Gasket", "cat": "เครื่องยนต์", "motos": "Wave 125i", "price": 95, "cost": 55, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "แกนสูบ", "name_en": "Cylinder", "cat": "เครื่องยนต์", "motos": "PCX 150", "price": 2800, "cost": 1800, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ฝาสูบ", "name_en": "Cylinder Head", "cat": "เครื่องยนต์", "motos": "Click 125i", "price": 3500, "cost": 2200, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ประเก็นเสื้อสูบ", "name_en": "Cylinder Gasket", "cat": "เครื่องยนต์", "motos": "Wave 110i,Wave 125i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ไส้กรองอากาศ", "name_en": "Air Filter", "cat": "กรอง/น้ำมัน", "motos": "Wave 110i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ไส้กรองน้ำมันเครื่อง", "name_en": "Oil Filter", "cat": "กรอง/น้ำมัน", "motos": "PCX 160,ADV 160", "price": 65, "cost": 35, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "กรองอากาศ Click", "name_en": "Air Filter Click", "cat": "กรอง/น้ำมัน", "motos": "Click 125i,Click 150i", "price": 130, "cost": 80, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ไส้กรองน้ำมัน CB", "name_en": "Oil Filter CB", "cat": "กรอง/น้ำมัน", "motos": "CB300R,CB500F", "price": 85, "cost": 50, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "กรองเบนซิน", "name_en": "Fuel Filter", "cat": "กรอง/น้ำมัน", "motos": "Wave 125i,Click 150i", "price": 95, "cost": 55, "min": 8, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ผ้าเบรกหน้า", "name_en": "Front Brake Pad", "cat": "ระบบเบรก", "motos": "Wave 125i,Wave 110i", "price": 220, "cost": 130, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ผ้าเบรกหลัง", "name_en": "Rear Brake Pad", "cat": "ระบบเบรก", "motos": "Wave 125i,Wave 110i", "price": 180, "cost": 100, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "จานเบรกหน้า", "name_en": "Front Brake Disc", "cat": "ระบบเบรก", "motos": "Click 150i,PCX 160", "price": 1200, "cost": 750, "min": 2, "type": "aftermarket", "brand": "Brembo"},
        {"name": "น้ำมันเบรก DOT4", "name_en": "Brake Fluid DOT4", "cat": "ระบบเบรก", "motos": "", "price": 150, "cost": 85, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สายเบรกหน้า", "name_en": "Front Brake Cable", "cat": "ระบบเบรก", "motos": "Wave 110i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "โซ่ขับ 428-120L", "name_en": "Drive Chain 428-120L", "cat": "ระบบส่งกำลัง", "motos": "Wave 125i", "price": 450, "cost": 280, "min": 3, "type": "aftermarket", "brand": "DID"},
        {"name": "สายพาน PCX", "name_en": "Drive Belt PCX", "cat": "ระบบส่งกำลัง", "motos": "PCX 160", "price": 1800, "cost": 1100, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สเตอร์หน้า 14T", "name_en": "Front Sprocket 14T", "cat": "ระบบส่งกำลัง", "motos": "Wave 125i", "price": 180, "cost": 100, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สเตอร์หลัง 35T", "name_en": "Rear Sprocket 35T", "cat": "ระบบส่งกำลัง", "motos": "Wave 125i", "price": 250, "cost": 150, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "แผ่นคลัช", "name_en": "Clutch Plate", "cat": "ระบบส่งกำลัง", "motos": "Wave 125i", "price": 380, "cost": 230, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ลูกปืนล้อหน้า", "name_en": "Front Wheel Bearing", "cat": "ระบบส่งกำลัง", "motos": "Wave 110i,Wave 125i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "NTN"},
        {"name": "สายพาน Click", "name_en": "Drive Belt Click", "cat": "ระบบส่งกำลัง", "motos": "Click 125i,Click 150i", "price": 1200, "cost": 750, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "หัวเทียน NGK CPR7EA-9", "name_en": "Spark Plug NGK CPR7EA-9", "cat": "ระบบไฟฟ้า", "motos": "Wave 110i,Wave 125i,Click 125i", "price": 120, "cost": 65, "min": 10, "type": "oem", "brand": "NGK"},
        {"name": "แบตเตอรี่ YTZ5S", "name_en": "Battery YTZ5S", "cat": "ระบบไฟฟ้า", "motos": "Wave 125i,Click 125i", "price": 850, "cost": 550, "min": 3, "type": "aftermarket", "brand": "YUASA"},
        {"name": "หลอดไฟหน้า LED", "name_en": "LED Headlight Bulb", "cat": "ระบบไฟฟ้า", "motos": "PCX 160,ADV 160", "price": 450, "cost": 280, "min": 5, "type": "aftermarket", "brand": "Philips"},
        {"name": "ไดชาร์จ", "name_en": "Stator Coil", "cat": "ระบบไฟฟ้า", "motos": "Wave 125i", "price": 1800, "cost": 1100, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "CDI", "name_en": "CDI Unit", "cat": "ระบบไฟฟ้า", "motos": "Wave 110i", "price": 950, "cost": 600, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "รีเลย์สตาร์ท", "name_en": "Starter Relay", "cat": "ระบบไฟฟ้า", "motos": "Click 150i,PCX 160", "price": 280, "cost": 170, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สวิทช์กุญแจ", "name_en": "Ignition Switch", "cat": "ระบบไฟฟ้า", "motos": "Wave 110i,Wave 125i", "price": 650, "cost": 400, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "โช้คหลัง", "name_en": "Rear Shock Absorber", "cat": "ช่วงล่าง", "motos": "Wave 110i,Wave 125i", "price": 950, "cost": 600, "min": 2, "type": "aftermarket", "brand": "YSS"},
        {"name": "ลูกปืนคอ", "name_en": "Steering Bearing", "cat": "ช่วงล่าง", "motos": "Wave 125i,Click 150i", "price": 180, "cost": 100, "min": 3, "type": "oem", "brand": "NTN"},
        {"name": "บุชยางแขนสวิง", "name_en": "Swing Arm Bush", "cat": "ช่วงล่าง", "motos": "Wave 110i,Wave 125i", "price": 85, "cost": 45, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "น้ำมันโช้ค", "name_en": "Fork Oil", "cat": "ช่วงล่าง", "motos": "CB300R", "price": 250, "cost": 150, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ยางนอก 80/90-17", "name_en": "Tire 80/90-17", "cat": "ยาง/ล้อ", "motos": "Wave 110i,Wave 125i", "price": 650, "cost": 400, "min": 4, "type": "aftermarket", "brand": "IRC"},
        {"name": "ยางนอก 90/90-14", "name_en": "Tire 90/90-14", "cat": "ยาง/ล้อ", "motos": "Click 125i,Click 150i", "price": 750, "cost": 480, "min": 4, "type": "aftermarket", "brand": "Michelin"},
        {"name": "ยางใน 17 นิ้ว", "name_en": "Inner Tube 17\"", "cat": "ยาง/ล้อ", "motos": "Wave 110i,Wave 125i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ซี่ลวดล้อหน้า", "name_en": "Front Spoke", "cat": "ยาง/ล้อ", "motos": "Wave 110i", "price": 350, "cost": 200, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ยางนอก 100/80-14", "name_en": "Tire 100/80-14", "cat": "ยาง/ล้อ", "motos": "PCX 160,ADV 160", "price": 980, "cost": 620, "min": 3, "type": "aftermarket", "brand": "Michelin"},
        {"name": "บังโคลนหน้า", "name_en": "Front Fender", "cat": "ตัวถัง/พลาสติก", "motos": "Wave 110i", "price": 480, "cost": 300, "min": 2, "type": "aftermarket", "brand": "NPP"},
        {"name": "ชุดสี (ฝาข้าง)", "name_en": "Side Cover Set", "cat": "ตัวถัง/พลาสติก", "motos": "Wave 125i", "price": 850, "cost": 550, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "เบาะนั่ง", "name_en": "Seat", "cat": "ตัวถัง/พลาสติก", "motos": "Click 150i", "price": 1200, "cost": 750, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "กระจกมองข้าง", "name_en": "Side Mirror", "cat": "ตัวถัง/พลาสติก", "motos": "", "price": 180, "cost": 100, "min": 5, "type": "aftermarket", "brand": "NPP"},
        {"name": "แฮนด์จับ", "name_en": "Handle Grip", "cat": "ตัวถัง/พลาสติก", "motos": "Wave 110i,Wave 125i", "price": 120, "cost": 70, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "หัวฉีด", "name_en": "Fuel Injector", "cat": "ระบบเชื้อเพลิง", "motos": "Click 125i,PCX 160", "price": 1500, "cost": 950, "min": 2, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ปั๊มเบนซิน", "name_en": "Fuel Pump", "cat": "ระบบเชื้อเพลิง", "motos": "Wave 125i,Click 150i", "price": 2200, "cost": 1400, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ก๊อกน้ำมัน", "name_en": "Fuel Cock", "cat": "ระบบเชื้อเพลิง", "motos": "", "price": 180, "cost": 100, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ท่อไอเสีย", "name_en": "Exhaust Pipe", "cat": "ท่อไอเสีย", "motos": "Wave 125i", "price": 1800, "cost": 1100, "min": 1, "type": "oem", "brand": "Honda Genuine"},
        {"name": "ปะเก็นท่อไอเสีย", "name_en": "Exhaust Gasket", "cat": "ท่อไอเสีย", "motos": "Wave 110i,Click 125i", "price": 65, "cost": 35, "min": 5, "type": "oem", "brand": "Honda Genuine"},
        {"name": "น้ำมันเครื่อง 10W-30 0.8L", "name_en": "Engine Oil 10W-30 0.8L", "cat": "น้ำมัน/สารหล่อลื่น", "motos": "Wave 110i,Wave 125i", "price": 180, "cost": 110, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "น้ำมันเครื่อง 10W-40 1L", "name_en": "Engine Oil 10W-40 1L", "cat": "น้ำมัน/สารหล่อลื่น", "motos": "PCX 160,CB300R,CB500F", "price": 280, "cost": 170, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "น้ำมันเกียร์ 80W-90", "name_en": "Gear Oil 80W-90", "cat": "น้ำมัน/สารหล่อลื่น", "motos": "Click 125i,PCX 160", "price": 120, "cost": 70, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "จาระบี", "name_en": "Grease", "cat": "น้ำมัน/สารหล่อลื่น", "motos": "", "price": 85, "cost": 45, "min": 10, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สายคันเร่ง", "name_en": "Throttle Cable", "cat": "สายควบคุม", "motos": "Wave 125i", "price": 150, "cost": 85, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สายครัช", "name_en": "Clutch Cable", "cat": "สายควบคุม", "motos": "Wave 125i", "price": 180, "cost": 100, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สายเบรกหลัง", "name_en": "Rear Brake Cable", "cat": "สายควบคุม", "motos": "Wave 110i", "price": 120, "cost": 70, "min": 3, "type": "oem", "brand": "Honda Genuine"},
        {"name": "สายไมล์", "name_en": "Speedometer Cable", "cat": "สายควบคุม", "motos": "Wave 110i,Wave 125i", "price": 130, "cost": 75, "min": 3, "type": "oem", "brand": "Honda Genuine"},
    ]

    created_part_ids = []
    for i, p in enumerate(parts):
        cat_id = cat_map.get(p['cat'])
        if not cat_id:
            print(f"  ⚠️ ไม่พบหมวดหมู่: {p['cat']}")
            continue

        # Find motorcycle IDs
        moto_ids = []
        if p['motos']:
            for mname in p['motos'].split(','):
                mname = mname.strip()
                # Partial match
                for key, mid in moto_map.items():
                    if mname.lower() in key.lower():
                        moto_ids.append(mid)
                        break

        vals = {
            'name': p['name'],
            'name_en': p['name_en'],
            'category_id': cat_id,
            'price': p['price'],
            'cost': p['cost'],
            'min_qty': p['min'],
            'part_type': p['type'],
            'quality_brand': p['brand'],
            'brand': 'Honda',
        }
        if moto_ids:
            vals['motorcycle_ids'] = [(6, 0, moto_ids)]

        try:
            pid = models.execute_kw(DB, uid, PASSWORD, 'spare.part', 'create', [vals])
            created_part_ids.append(pid)
            print(f"  ✅ [{i+1}/{len(parts)}] {p['name']} (id={pid})")
        except Exception as e:
            print(f"  ❌ {p['name']}: {e}")
            created_part_ids.append(None)

    return created_part_ids

def import_stock_moves(uid, models, part_ids):
    """สร้างข้อมูลการเบิกเข้า-ออก"""
    # ดึงรายการ part ทั้งหมด
    all_parts = models.execute_kw(DB, uid, PASSWORD, 'spare.part', 'search_read', [[]], {'fields': ['id', 'name']})
    if not all_parts:
        print("❌ ไม่พบข้อมูลอะไหล่")
        return

    print(f"\n📦 พบอะไหล่ {len(all_parts)} รายการ")

    base = datetime(2026, 1, 5)

    # === รับเข้า (Stock In) ===
    print("\n🟢 สร้างข้อมูลรับเข้า...")
    in_count = 0
    for i, part in enumerate(all_parts):
        qty = random.choice([10, 15, 20, 25, 30, 50])
        date = (base + timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S")
        vals = {
            'part_id': part['id'],
            'qty': qty,
            'move_type': 'in',
            'state': 'done',
            'date': date,
            'reference': f"PO-2026-{str(i+1).zfill(3)}",
            'note': f"รับเข้าสต็อก {part['name']}",
        }
        try:
            models.execute_kw(DB, uid, PASSWORD, 'spare.stock.move', 'create', [vals])
            in_count += 1
        except Exception as e:
            print(f"  ❌ IN {part['name']}: {e}")

    # เพิ่มรอบ 2 (30 รายการแรก)
    for i, part in enumerate(all_parts[:30]):
        qty = random.choice([5, 10, 15, 20])
        date = (base + timedelta(days=random.randint(60, 120))).strftime("%Y-%m-%d %H:%M:%S")
        vals = {
            'part_id': part['id'],
            'qty': qty,
            'move_type': 'in',
            'state': 'done',
            'date': date,
            'reference': f"PO-2026-{str(len(all_parts)+i+1).zfill(3)}",
            'note': f"เติมสต็อก {part['name']}",
        }
        try:
            models.execute_kw(DB, uid, PASSWORD, 'spare.stock.move', 'create', [vals])
            in_count += 1
        except Exception as e:
            print(f"  ❌ IN2 {part['name']}: {e}")
    print(f"  ✅ สร้างรับเข้า {in_count} รายการ")

    # === เบิกออก (Stock Out) ===
    print("\n🟠 สร้างข้อมูลเบิกออก...")
    reasons = ["ซ่อมรถลูกค้า", "เปลี่ยนตามระยะ", "ซ่อมบำรุง", "ขายหน้าร้าน", "เคลม"]
    out_count = 0
    for i in range(50):
        part = random.choice(all_parts)
        qty = random.choice([1, 2, 3, 4, 5])
        date = (base + timedelta(days=random.randint(10, 120))).strftime("%Y-%m-%d %H:%M:%S")
        reason = random.choice(reasons)
        vals = {
            'part_id': part['id'],
            'qty': qty,
            'move_type': 'out',
            'state': 'done',
            'date': date,
            'reference': f"SO-2026-{str(i+1).zfill(3)}",
            'note': f"{reason} - {part['name']}",
        }
        try:
            models.execute_kw(DB, uid, PASSWORD, 'spare.stock.move', 'create', [vals])
            out_count += 1
        except Exception as e:
            print(f"  ❌ OUT {part['name']}: {e}")
    print(f"  ✅ สร้างเบิกออก {out_count} รายการ")

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Import ข้อมูลอะไหล่เข้า Odoo")
    print("=" * 50)

    uid, models = connect()

    print("\n📋 กำลัง import อะไหล่...")
    part_ids = import_parts(uid, models)

    print("\n📋 กำลัง import การเบิกเข้า-ออก...")
    import_stock_moves(uid, models, part_ids)

    print("\n" + "=" * 50)
    print("🎉 Import เสร็จสิ้น!")
    print("=" * 50)
