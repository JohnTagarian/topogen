# คู่มือระบบ (System Manual) — AI Network Topology Generator

**เวอร์ชัน:** 1.0  
**ปรับปรุงล่าสุด:** เมษายน 2568  
**สำหรับ:** นักพัฒนาและผู้ดูแลระบบ

---

## สารบัญ

1. [ภาพรวมสถาปัตยกรรม](#1-ภาพรวมสถาปัตยกรรม)
2. [โครงสร้างโปรเจกต์](#2-โครงสร้างโปรเจกต์)
3. [การติดตั้งระบบ](#3-การติดตั้งระบบ)
4. [การตั้งค่า Environment Variables](#4-การตั้งค่า-environment-variables)
5. [รายละเอียดแต่ละโมดูล](#5-รายละเอียดแต่ละโมดูล)
6. [Data Structures และ Schemas](#6-data-structures-และ-schemas)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Equipment Database](#8-equipment-database)
9. [API Endpoints](#9-api-endpoints)
10. [การแก้ไขปัญหาที่พบบ่อย](#10-การแก้ไขปัญหาที่พบบ่อย)
11. [การพัฒนาต่อในอนาคต](#11-การพัฒนาต่อในอนาคต)

---

## 1. ภาพรวมสถาปัตยกรรม

### Stack

| ชั้น | เทคโนโลยี | บทบาท |
|---|---|---|
| **Backend** | Python 3.8+, Flask | Web server, routing, template rendering |
| **AI / LLM** | DeepSeek API (via LangChain) | Natural language processing, topology design |
| **Frontend** | Tailwind CSS, Vanilla JS | UI, interactivity |
| **Graph** | Cytoscape.js + dagre | Interactive network diagram |
| **Font** | Kanit (Google Fonts) | Thai-optimized typography |

### Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                             │
│    GET /          POST /generate          result.html           │
└──────┬───────────────────┬────────────────────────┬─────────────┘
       │                   │                        │
       ▼                   ▼                        │
┌─────────────────────────────────────────┐         │
│              app.py (Flask)             │         │
│  index()   │   generate()              │         │
└─────────────────────────────────────────┘         │
                      │                             │
         ┌────────────┼────────────┐                │
         ▼            ▼            ▼                │
    ┌─────────┐  ┌─────────┐  ┌────────┐           │
    │  llm.py │  │  bom.py │  │diagram │           │
    │ Stage 1 │  │generate │  │  .py   │           │
    │ Stage 2 │  │  _bom() │  │(helper)│           │
    └────┬────┘  └────┬────┘  └────────┘           │
         │            │                             │
         ▼            ▼                             │
    ┌──────────┐  ┌───────────────┐                │
    │ DeepSeek │  │ equipment.json│                │
    │   API    │  │  (DB ราคา)   │                │
    └──────────┘  └───────────────┘                │
                                                    │
         topology + bom + parsed_params ────────────┘
                                           render_template
```

### Two-Stage AI Pipeline

```
User Input (Thai/English text)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STAGE 1: parse_requirements()                              │
  │  DeepSeek → Extract structured params from natural language │
  │  Output: organization_type, num_users, services, budget…    │
  └─────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STAGE 2: design_topology()                                 │
  │  DeepSeek → Design network topology from structured params  │
  │  Output: nodes[], links[], subnets[], notes                 │
  └─────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  generate_bom()                                             │
  │  Match nodes → equipment.json → calculate pricing           │
  │  Output: items[], total_thb                                 │
  └─────────────────────────────────────────────────────────────┘
```

---

## 2. โครงสร้างโปรเจกต์

```
topogen/
├── app.py                  # Flask application, routes
├── llm.py                  # DeepSeek LLM integration (2-stage pipeline)
├── bom.py                  # Bill of Materials generator
├── diagram.py              # Cytoscape.js elements helper
├── prompts.py              # LLM system/user prompt templates
├── equipment.json          # Equipment catalog with pricing (THB)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (ห้าม commit)
├── templates/
│   ├── index.html          # หน้าหลัก — input form (Tailwind CSS)
│   └── result.html         # หน้าผลลัพธ์ (Tailwind CSS + Cytoscape.js)
├── static/
│   └── style.css           # CSS เพิ่มเติม (ไม่ได้ใช้ใน result.html แล้ว)
├── USER_MANUAL.md          # คู่มือผู้ใช้งาน
└── SYSTEM_MANUAL.md        # คู่มือระบบ (ไฟล์นี้)
```

---

## 3. การติดตั้งระบบ

### ความต้องการของระบบ

- Python 3.8 หรือสูงกว่า
- pip
- การเชื่อมต่ออินเทอร์เน็ต (สำหรับ DeepSeek API และ CDN)
- DeepSeek API Key

### ขั้นตอนการติดตั้ง

**1. Clone หรือ download โปรเจกต์**

```bash
cd /path/to/your/projects
# clone หรือ unzip project ที่นี่
cd topogen
```

**2. สร้าง Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

**3. ติดตั้ง Dependencies**

```bash
pip install -r requirements.txt
```

**4. สร้างไฟล์ `.env`**

```bash
cp .env.example .env            # ถ้ามี example
# หรือสร้างใหม่
```

แก้ไขค่าใน `.env` (ดูรายละเอียดใน [Section 4](#4-การตั้งค่า-environment-variables))

**5. รันเซิร์ฟเวอร์**

```bash
# Development
python app.py

# หรือใช้ flask CLI
flask run --host=0.0.0.0 --port=5000
```

**6. เปิดเบราว์เซอร์**

```
http://localhost:5000
```

### Production Deployment (แนะนำ)

```bash
# ใช้ Gunicorn สำหรับ production
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

---

## 4. การตั้งค่า Environment Variables

ไฟล์ `.env` ต้องอยู่ที่ root ของโปรเจกต์ (**ห้าม commit ขึ้น Git**)

```dotenv
# DeepSeek API Configuration
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

| Variable | Required | Default | คำอธิบาย |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | **Yes** | — | API key จาก platform.deepseek.com |
| `DEEPSEEK_BASE_URL` | No | `https://api.deepseek.com` | Base URL ของ API |
| `DEEPSEEK_MODEL` | No | `deepseek-chat` | Model ที่จะใช้ |

> **หมายเหตุ:** เนื่องจาก LangChain ใช้ `ChatOpenAI` ที่ compatible กับ OpenAI format ระบบสามารถเปลี่ยนไปใช้ OpenAI หรือ LLM อื่นที่ compatible ได้โดยเปลี่ยน `DEEPSEEK_BASE_URL` และ `DEEPSEEK_API_KEY`

---

## 5. รายละเอียดแต่ละโมดูล

### 5.1 `app.py` — Flask Application

**Imports:**
```python
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv
```

**Custom Filter:**
```python
@app.template_filter("thousands")
def thousands_filter(value):
    return "{:,}".format(int(value))
# ใช้ใน template: {{ 45000 | thousands }}  →  "45,000"
```

**Routes:**

| Route | Method | Function | คำอธิบาย |
|---|---|---|---|
| `/` | GET | `index()` | แสดงหน้า input form |
| `/generate` | POST | `generate()` | รับ requirement → run pipeline → แสดงผล |
| `/health` | GET | `health()` | Health check (returns `{"status": "ok"}`) |

**`generate()` endpoint — ลำดับการทำงาน:**

```python
1. รับ user_input จาก form (POST body)
2. Validate: ถ้าว่างเปล่า → return error ที่ index.html
3. parse_requirements(user_input)   # Stage 1 LLM call
4. design_topology(parsed_params)   # Stage 2 LLM call
5. generate_bom(topology)           # equipment.json lookup
6. render_template("result.html",
       topology=topology,
       topology_json=json.dumps(topology),  # สำหรับ Cytoscape.js
       bom=bom,
       parsed_params=parsed_params,
       user_input=user_input)
```

---

### 5.2 `llm.py` — LLM Integration

**LLM Client (Singleton):**
```python
_client = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.3,   # ค่าต่ำ = ผลลัพธ์ deterministic มากขึ้น
    max_tokens=4096,
)
```

**`_parse_json_response(text)`:**
- Strip markdown code fences (` ```json ... ``` `) ก่อน parse
- ใช้ regex: `r"```(?:json)?\s*(.*?)```"`
- Return `dict` จาก `json.loads()`

**`parse_requirements(user_input) → dict`:**
- ส่ง STAGE1_SYSTEM + STAGE1_USER ไปยัง DeepSeek
- Input: free text (Thai/English)
- Output: structured dict (9 fields, ดู Section 6)

**`design_topology(parsed_params) → dict`:**
- ส่ง STAGE2_SYSTEM + STAGE2_USER ไปยัง DeepSeek
- Input: parsed dict จาก Stage 1 (เป็น JSON string)
- Output: topology dict (nodes, links, subnets, notes)

---

### 5.3 `prompts.py` — LLM Prompts

**STAGE1_SYSTEM** — System prompt สำหรับ parsing:
- สั่งให้ LLM extract 9 fields จาก natural language
- กำหนด enum values (เช่น organization_type, security_level)
- สั่ง "Respond ONLY with valid JSON. No markdown fences"

**STAGE2_SYSTEM** — System prompt สำหรับ topology design:
- กำหนด JSON schema สำหรับ output (nodes, links, subnets)
- กำหนด enum values ทั้งหมด (node type, layer, link_type, model_hint)
- กำหนด Design Rules 8 ข้อ:

| Rule | เงื่อนไข | การกระทำ |
|---|---|---|
| 1 | num_users > 20 | ใช้ Hierarchical design (core → distribution → access) |
| 2 | num_users < 20 | Flat star topology |
| 3 | security_level = moderate/high | ใส่ firewall node |
| 4 | redundancy_needed = true | ใส่ redundant links |
| 5 | "wifi" in required_services | ใส่ access_point nodes |
| 6 | เสมอ | ใส่ cloud node สำหรับ ISP |
| 7 | เสมอ | Keep minimal — อย่า over-design |
| 8 | เสมอ | Node labels ต้องเป็นภาษาอังกฤษ |

**การแก้ไข Prompts:**  
แก้ไขไฟล์ `prompts.py` โดยตรง ไม่ต้อง restart server ถ้า import ทำงานในแต่ละ request  
(ปัจจุบัน `llm.py` ถูก import ใน `generate()` function ทำให้ reload ได้โดยไม่ต้อง restart)

---

### 5.4 `bom.py` — Bill of Materials Generator

**Equipment DB (Singleton):**
```python
_EQUIPMENT_DB = None  # โหลดครั้งแรกแล้ว cache ไว้

def _load_db() -> dict:
    # โหลด equipment.json จาก same directory
    db_path = os.path.join(os.path.dirname(__file__), "equipment.json")
```

**`generate_bom(topology) → dict`:**

1. วน loop ผ่าน `topology["nodes"]`
2. ดึง `node["specs"]["model_hint"]` แต่ละโหนด
3. นับจำนวน (hint_counts dict)
4. Lookup ราคาจาก `equipment.json`
5. คำนวณ subtotal = unit_price × qty
6. Sort by subtotal descending

**Handling Unknown Equipment:**
```python
# ถ้า model_hint ไม่อยู่ใน equipment.json
items.append({
    "name": f"Unknown ({hint})",
    "brand": "-",
    "unit_price_thb": 0,
    "subtotal_thb": 0,
})
```

---

### 5.5 `diagram.py` — Visualization Helper

ฟังก์ชัน `topology_to_cytoscape_elements()` ช่วย convert topology dict → Cytoscape.js elements JSON

> **หมายเหตุ:** ปัจจุบัน `result.html` สร้าง elements โดยตรงใน JavaScript โดยไม่ผ่าน `diagram.py` ไฟล์นี้เหลือไว้เป็น utility helper สำหรับ server-side use ในอนาคต

---

## 6. Data Structures และ Schemas

### Stage 1 Output — Parsed Requirements

```json
{
  "organization_type": "office",
  "num_users": 90,
  "num_locations": 3,
  "area_sqm": 2000,
  "required_services": ["internet", "wifi", "voip", "file_sharing"],
  "security_level": "moderate",
  "budget_thb": 500000,
  "redundancy_needed": false,
  "internet_bandwidth": "100Mbps",
  "special_requirements": "ต้องการรองรับการขยายในอนาคต"
}
```

| Field | Type | Values |
|---|---|---|
| `organization_type` | string | `office`, `school`, `factory`, `home`, `datacenter`, `retail`, `hospital` |
| `num_users` | integer | จำนวนผู้ใช้ |
| `num_locations` | integer | จำนวน site/อาคาร |
| `area_sqm` | integer \| null | ขนาดพื้นที่ (ตร.ม.) |
| `required_services` | string[] | `internet`, `file_sharing`, `voip`, `cctv`, `wifi` |
| `security_level` | string | `basic`, `moderate`, `high` |
| `budget_thb` | integer \| null | งบประมาณ (บาท) |
| `redundancy_needed` | boolean | ต้องการ redundant links |
| `internet_bandwidth` | string \| null | เช่น `"100Mbps"` |
| `special_requirements` | string \| null | ข้อกำหนดพิเศษ |

---

### Stage 2 Output — Topology

```json
{
  "topology_name": "3-Floor Office Network",
  "topology_type": "tree",
  "nodes": [
    {
      "id": "cloud-1",
      "label": "Internet / ISP",
      "type": "cloud",
      "layer": "core",
      "specs": {
        "model_hint": null,
        "ports_needed": 1,
        "bandwidth": "100Mbps"
      }
    },
    {
      "id": "fw-1",
      "label": "Firewall",
      "type": "firewall",
      "layer": "core",
      "specs": {
        "model_hint": "enterprise_firewall",
        "ports_needed": 6,
        "bandwidth": "1Gbps"
      }
    }
  ],
  "links": [
    {
      "source": "cloud-1",
      "target": "fw-1",
      "link_type": "ethernet",
      "bandwidth": "100Mbps",
      "label": "WAN"
    }
  ],
  "subnets": [
    {
      "name": "LAN-Floor1",
      "cidr": "192.168.1.0/24",
      "vlan_id": 10,
      "node_ids": ["sw-f1", "ap-1"]
    }
  ],
  "notes": "Three-tier hierarchical design. Each floor has dedicated PoE switch for access points and VoIP phones."
}
```

**Node Types และ Layer Mapping:**

| type | layer ปกติ | ไอคอน |
|---|---|---|
| `cloud` | core | เมฆ (เทา) |
| `firewall` | core | กล่องแดง |
| `router` | core / distribution | วงกลมน้ำเงิน |
| `switch` | distribution / access | สี่เหลี่ยมเขียว |
| `server` | access / endpoint | กล่องเทาเข้ม |
| `access_point` | access | เส้นโค้งน้ำเงิน |
| `pc` | endpoint | จอคอม |
| `printer` | endpoint | เครื่องพิมพ์ |
| `ups` | core / access | สายฟ้าส้ม |

**Link Types:**

| link_type | เส้น | สี |
|---|---|---|
| `ethernet` | ทึบ | เทา (#94a3b8) |
| `fiber` | ทึบ | เทา (#94a3b8) |
| `wireless` | ประ | ฟ้า (#60a5fa) |
| `vpn` | ประ | ฟ้า (#60a5fa) |

---

### BOM Output

```json
{
  "items": [
    {
      "model_hint": "core_switch",
      "name": "Cisco Catalyst 9300-48T",
      "brand": "Cisco",
      "category": "Switch",
      "specs": "48x GE, 4x 10G SFP+, L3, stackable",
      "qty": 1,
      "unit_price_thb": 85000,
      "subtotal_thb": 85000
    }
  ],
  "total_thb": 387500
}
```

---

## 7. Frontend Architecture

### index.html

| Element | Tech | คำอธิบาย |
|---|---|---|
| Styling | Tailwind CSS (CDN) | Utility-first CSS |
| Font | Kanit (Google Fonts) | Thai-optimized, weights 300–700 |
| Form | HTML5 `<form>` | POST to `/generate` |
| JS | Vanilla JS | Pill click, clear btn, loading state |

**Custom CSS Classes (ใน `<style>` tag):**

```css
.text-gradient        /* AI text — cyan→blue gradient clip */
.textarea-glow        /* Focus ring glow effect */
.btn-gradient         /* Submit button gradient + hover/disabled states */
```

**JavaScript Logic:**
```javascript
// 1. Show/hide clear button when textarea has content
textarea.addEventListener('input', updateClearBtn)

// 2. Clear button resets textarea
clearBtn.addEventListener('click', () => { textarea.value = ''; })

// 3. Example pills insert text
document.querySelectorAll('.pill-btn').forEach(btn => {
  btn.addEventListener('click', () => { textarea.value = btn.textContent })
})

// 4. Loading state on submit
form.addEventListener('submit', () => {
  submitBtn.disabled = true
  // show spinner, hide icon, change text
})
```

---

### result.html

| Element | Tech | เวอร์ชัน |
|---|---|---|
| Styling | Tailwind CSS (CDN) | latest |
| Font | Kanit (Google Fonts) | weights 300–700 |
| Graph | Cytoscape.js | 3.30.4 |
| Layout | dagre | 0.8.5 |
| Layout plugin | cytoscape-dagre | 2.5.0 |

**Template Variables ที่ใช้:**

| Variable | Type | ใช้ใน |
|---|---|---|
| `topology` | dict | แสดงชื่อ, type, subnets, notes |
| `topology_json` | string (JSON) | `var topoData = {{ topology_json \| safe }}` |
| `bom` | dict | ตาราง BOM, CSV export |
| `parsed_params` | dict | Debug section |
| `user_input` | string | (ส่งมาแต่ไม่แสดงใน result) |
| `error` | string \| None | แสดง error box ถ้ามี |

**Cytoscape.js Configuration:**

```javascript
window.cy = cytoscape({
  container: document.getElementById('cy-container'),
  layout: {
    name: 'dagre',
    rankDir: 'TB',         // Top-to-Bottom
    nodeSep: 60,           // ระยะห่างโหนดในแนวนอน
    rankSep: 100,          // ระยะห่างระหว่าง layer
    sort: (a, b) => a.data('layerRank') - b.data('layerRank')
  },
  minZoom: 0.3,
  maxZoom: 3,
  wheelSensitivity: 0.3
})
```

**Layer Rank สำหรับ Sorting:**

```javascript
var LAYER_ORDER = { 'core': 0, 'distribution': 1, 'access': 2, 'endpoint': 3 }
```

**SVG Icons:** Inline SVG ฝังอยู่ใน JavaScript เป็น string แล้ว encode เป็น base64 data URI ก่อนส่งให้ Cytoscape เป็น `background-image`

**Export Functions:**

```javascript
// PNG Export
document.getElementById('btn-save-png').addEventListener('click', () => {
  const png = window.cy.png({ output: 'base64uri', bg: '#f8fafc', scale: 2, full: true })
  // trigger download ด้วย <a> element
})

// CSV Export
document.getElementById('btn-save-csv').addEventListener('click', () => {
  const bomData = {{ bom | tojson }}  // Jinja2 inject
  // สร้าง CSV rows, escape commas/quotes
  // ใส่ '\uFEFF' BOM สำหรับ Excel UTF-8 compatibility
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
})
```

---

## 8. Equipment Database

ไฟล์ `equipment.json` เป็น lookup table สำหรับ BOM generation

### โครงสร้าง

```json
{
  "<model_hint>": {
    "name": "ชื่อรุ่น",
    "brand": "ยี่ห้อ",
    "category": "ประเภท",
    "price_thb": 12345,
    "specs": "รายละเอียดสเปค"
  }
}
```

### รายการอุปกรณ์ปัจจุบัน

| model_hint | ยี่ห้อ / รุ่น | ราคา (฿) | Category |
|---|---|---|---|
| `enterprise_router` | Cisco ISR 4331 | 45,000 | Router |
| `smb_router` | MikroTik hAP ax3 | 3,500 | Router |
| `core_switch` | Cisco Catalyst 9300-48T | 85,000 | Switch |
| `access_switch` | Cisco Catalyst 1000-24T | 12,000 | Switch |
| `poe_switch` | Cisco CBS250-24P | 18,000 | Switch (PoE) |
| `enterprise_firewall` | Fortinet FortiGate 60F | 35,000 | Firewall |
| `smb_firewall` | Fortinet FortiGate 40F | 15,000 | Firewall |
| `rack_server` | Dell PowerEdge R350 | 55,000 | Server |
| `access_point` | Ubiquiti U6-Pro | 5,500 | Access Point |
| `ups` | APC Smart-UPS 1500VA | 15,000 | UPS |

### การเพิ่มอุปกรณ์ใหม่

1. เปิดไฟล์ `equipment.json`
2. เพิ่ม entry ใหม่ด้วย key ที่เป็น `model_hint` ใหม่:

```json
{
  "my_new_device": {
    "name": "ชื่อรุ่น",
    "brand": "ยี่ห้อ",
    "category": "Switch",
    "price_thb": 25000,
    "specs": "24x GE, managed"
  }
}
```

3. เพิ่ม `model_hint` ใหม่ใน `STAGE2_SYSTEM` ใน `prompts.py` เพื่อให้ LLM รู้จักและใช้งานได้:

```python
# ใน prompts.py, ส่วน specs.model_hint
"model_hint": "<enterprise_router|smb_router|...|my_new_device>"
```

---

## 9. API Endpoints

### `GET /`
- **Response:** HTML (index.html)
- **Template vars:** `error` (optional, แสดง error จาก query string)

### `POST /generate`

**Request:**
```
Content-Type: application/x-www-form-urlencoded

user_input=ออฟฟิศ 3 ชั้น พนักงาน 90 คน...
```

**Response (Success):** HTML (result.html) พร้อม template variables:
- `topology` — dict
- `topology_json` — JSON string
- `bom` — dict
- `parsed_params` — dict
- `user_input` — string

**Response (Error):** HTML (result.html) พร้อม `error` string

**Error conditions:**
- `user_input` ว่างเปล่า → redirect กลับ index.html พร้อม error
- LLM API error → result.html พร้อม error message
- JSON parse error จาก LLM → result.html พร้อม error message

### `GET /health`

**Response:**
```json
{"status": "ok"}
```

---

## 10. การแก้ไขปัญหาที่พบบ่อย

### ปัญหา: เกิด Error "เกิดข้อผิดพลาด" บนหน้า result.html

**สาเหตุที่พบบ่อย:**

1. **API Key ผิด / หมดอายุ**
   ```bash
   # ตรวจสอบ .env
   cat .env | grep DEEPSEEK_API_KEY
   # ทดสอบ key ด้วย curl
   curl https://api.deepseek.com/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

2. **LLM ตอบกลับไม่ใช่ JSON**  
   LLM บางครั้งเพิ่ม text นอก JSON schema  
   แก้ไข: ตรวจสอบ `_parse_json_response()` ใน `llm.py` หรือทำให้ prompt เข้มงวดขึ้น

3. **Network timeout**  
   เพิ่ม timeout ใน LLM client:
   ```python
   _client = ChatOpenAI(
       ...,
       timeout=60,          # เพิ่มเป็น 60 วินาที
       max_retries=2,
   )
   ```

---

### ปัญหา: กราฟไม่แสดง หรือแสดงว่างเปล่า

**ตรวจสอบ:**

1. เปิด Browser DevTools (F12) → Console ดู JavaScript errors
2. ตรวจสอบว่า CDN โหลดได้ (ต้องต่ออินเทอร์เน็ต):
   - `https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.4/cytoscape.min.js`
   - `https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js`
   - `https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js`
3. ตรวจสอบ `topology_json` ใน Raw Topology JSON section ว่ามี nodes และ links

---

### ปัญหา: ไฟล์ CSV ภาษาไทยเสียใน Excel

ไฟล์ใส่ UTF-8 BOM (`\uFEFF`) ไว้แล้ว ถ้ายังเสียให้:
- เปิดผ่าน Google Sheets แทน
- หรือ Excel: Data → From Text/CSV → File Origin: 65001 (UTF-8)

---

### ปัญหา: `ModuleNotFoundError` ตอนรัน

```bash
# ตรวจสอบว่า activate venv แล้ว
which python  # ควรชี้ไปที่ venv/bin/python

# ติดตั้ง dependencies ใหม่
pip install -r requirements.txt
```

---

### ปัญหา: Port 5000 ถูกใช้งานอยู่แล้ว

```bash
# macOS/Linux
lsof -i :5000
kill -9 <PID>

# หรือเปลี่ยน port
flask run --port=5001
```

---

## 11. การพัฒนาต่อในอนาคต

### แนวทางที่แนะนำ

| Feature | แนวทาง |
|---|---|
| **บันทึกประวัติการออกแบบ** | เพิ่ม SQLite database + history page |
| **เพิ่มอุปกรณ์ใน BOM** | แก้ `equipment.json` + อัปเดต prompt ใน `prompts.py` |
| **เปลี่ยน LLM Provider** | แก้ `llm.py`: เปลี่ยน `base_url` + `api_key` + `model` ใน `.env` |
| **Export เป็น PDF** | ใช้ `weasyprint` หรือ `pdfkit` + เพิ่ม route `/export/pdf` |
| **รองรับ Multi-site topology** | ขยาย Stage 2 prompt ให้รู้จัก WAN link ระหว่าง site |
| **Authentication** | เพิ่ม Flask-Login + user session |
| **Rate limiting** | ใช้ Flask-Limiter ป้องกัน API abuse |

### การเพิ่ม LLM Provider ใหม่

เนื่องจากระบบใช้ `langchain_openai.ChatOpenAI` สามารถเปลี่ยนไปใช้ provider อื่นได้โดยแก้ `.env`:

```dotenv
# ตัวอย่าง: เปลี่ยนไปใช้ OpenAI
DEEPSEEK_API_KEY=sk-openai-key-here
DEEPSEEK_BASE_URL=https://api.openai.com/v1
DEEPSEEK_MODEL=gpt-4o

# ตัวอย่าง: ใช้ OpenRouter
DEEPSEEK_API_KEY=sk-or-xxxx
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MODEL=anthropic/claude-3.5-sonnet
```

### Dependencies ปัจจุบัน

```
flask                    Web framework
langchain==0.2.17        LLM orchestration
langchain-openai==0.1.25 OpenAI-compatible LLM client
python-dotenv            .env loader
```

> **หมายเหตุ:** `langchain` และ `langchain-openai` มี version pinned เพราะ API เปลี่ยนบ่อย ควรทดสอบก่อน upgrade

---

*AI Network Topology Generator v1.0 — System Manual*  
*สำหรับข้อสงสัยเพิ่มเติม ติดต่อทีมพัฒนา*
