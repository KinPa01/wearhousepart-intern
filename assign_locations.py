# -*- coding: utf-8 -*-
"""
Script: Assign ตำแหน่งจัดเก็บให้อะไหล่ทุกตัวตามหมวดหมู่
- เครื่องยนต์, ระบบส่งกำลัง, ท่อไอเสีย → โซน A
- ระบบเบรก → โซน B
- ระบบไฟฟ้า, สายควบคุม → โซน C
- ตัวถัง/พลาสติก → โซน D
- ยาง/ล้อ, ช่วงล่าง → โซน E
- กรอง/น้ำมัน, น้ำมัน/สารหล่อลื่น, ระบบเชื้อเพลิง → โซน F
"""
import xmlrpc.client

URL = 'http://localhost:8044'
DB = 'odoo'
USER = 'admin'
PASS = 'admin'

# --- Connect ---
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def search_read(model, domain, fields):
    return models.execute_kw(DB, uid, PASS, model, 'search_read', [domain], {'fields': fields})

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

# --- 1. ดึงข้อมูล Location ทั้งหมด (shelf level) ---
locations = search_read('spare.location', [('location_type', '=', 'shelf')],
                        ['id', 'name', 'complete_code', 'parent_id', 'category_id'])

# ดึง Zone ด้วย
zones = search_read('spare.location', [('location_type', '=', 'zone')],
                    ['id', 'name', 'code', 'category_id'])

print("=== โซนที่มี ===")
for z in zones:
    cat_name = z['category_id'][1] if z['category_id'] else '-'
    print(f"  {z['code']} - {z['name']} (หมวด: {cat_name})")

print(f"\n=== ชั้นวาง (shelf) ที่มี: {len(locations)} ===")
for loc in locations:
    print(f"  {loc['complete_code']} - {loc['name']}")

# --- 2. สร้าง mapping: ชื่อหมวดหมู่ → Zone code ---
CATEGORY_TO_ZONE = {
    'เครื่องยนต์': 'A',
    'ระบบส่งกำลัง': 'A',
    'ท่อไอเสีย': 'A',
    'ระบบเบรก': 'B',
    'ระบบไฟฟ้า': 'C',
    'สายควบคุม': 'C',
    'ตัวถัง/พลาสติก': 'D',
    'ยาง/ล้อ': 'E',
    'ช่วงล่าง': 'E',
    'กรอง/น้ำมัน': 'F',
    'น้ำมัน/สารหล่อลื่น': 'F',
    'ระบบเชื้อเพลิง': 'F',
}

# --- 3. สร้าง mapping: Zone code → [shelf_ids] ---
zone_map = {}  # code -> zone_id
for z in zones:
    zone_map[z['code']] = z['id']

zone_shelves = {}  # zone_code -> [shelf records]
for loc in locations:
    parent_id = loc['parent_id'][0] if loc['parent_id'] else None
    for z in zones:
        if z['id'] == parent_id:
            zone_shelves.setdefault(z['code'], []).append(loc)
            break

print("\n=== Mapping Zone → Shelves ===")
for code, shelves in sorted(zone_shelves.items()):
    print(f"  Zone {code}: {[s['complete_code'] for s in shelves]}")

# --- 4. ดึงหมวดหมู่ ---
categories = search_read('spare.category', [], ['id', 'name'])
cat_id_to_name = {c['id']: c['name'] for c in categories}

# --- 5. ดึงอะไหล่ทั้งหมด ---
parts = search_read('spare.part', [], ['id', 'name', 'code', 'category_id', 'location_id'])
print(f"\n=== อะไหล่ทั้งหมด: {len(parts)} ชิ้น ===")

# --- 6. Assign location ---
assigned = 0
skipped = 0
errors = 0
zone_counters = {}  # track which shelf index to use next per zone

for part in parts:
    cat_id = part['category_id'][0] if part['category_id'] else None
    cat_name = part['category_id'][1] if part['category_id'] else 'ไม่มีหมวด'

    # หา zone code
    zone_code = CATEGORY_TO_ZONE.get(cat_name)
    if not zone_code:
        print(f"  ⚠️  ไม่พบ zone สำหรับ [{part['code']}] {part['name']} (หมวด: {cat_name})")
        errors += 1
        continue

    # หา shelf ใน zone (กระจายอะไหล่ไปแต่ละ shelf)
    shelves = zone_shelves.get(zone_code, [])
    if not shelves:
        print(f"  ⚠️  ไม่มี shelf ใน Zone {zone_code} สำหรับ [{part['code']}]")
        errors += 1
        continue

    # Round-robin: กระจายอะไหล่ไปแต่ละชั้นใน zone
    idx = zone_counters.get(zone_code, 0)
    shelf = shelves[idx % len(shelves)]
    zone_counters[zone_code] = idx + 1

    # เขียน location_id
    write('spare.part', [part['id']], {'location_id': shelf['id']})
    assigned += 1
    print(f"  ✅ [{part['code']}] {part['name']} → {shelf['complete_code']}")

print(f"\n{'='*50}")
print(f"✅ Assign สำเร็จ: {assigned} ชิ้น")
print(f"⚠️  ไม่สามารถ assign: {errors} ชิ้น")
print(f"รวมทั้งหมด: {len(parts)} ชิ้น")
