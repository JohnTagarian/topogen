# คู่มือระบบ (System Manual)
## AI Network Topology Generator

**เวอร์ชัน:** 1.0  
**วันที่:** เมษายน 2568  
**กลุ่มเป้าหมาย:** Developer, System Administrator

---

## สารบัญ

1. [ภาพรวมสถาปัตยกรรม](#1-ภาพรวมสถาปัตยกรรม)
2. [โครงสร้างไฟล์](#2-โครงสร้างไฟล์)
3. [Technology Stack และ Dependencies](#3-technology-stack-และ-dependencies)
4. [การติดตั้งระบบ](#4-การติดตั้งระบบ)
5. [การตั้งค่า Environment Variables](#5-การตั้งค่า-environment-variables)
6. [การทำงานของแต่ละ Module](#6-การทำงานของแต่ละ-module)
7. [LLM Prompt Design](#7-llm-prompt-design)
8. [Topology JSON Schema](#8-topology-json-schema)
9. [Equipment Database](#9-equipment-database)
10. [Flask Routes และ Pipeline](#10-flask-routes-และ-pipeline)
11. [Diagram Generation](#11-diagram-generation)
12. [การทดสอบ](#12-การทดสอบ)
13. [การดูแลรักษาและแก้ไขปัญหา](#13-การดูแลรักษาและแก้ไขปัญหา)
14. [การขยายระบบในอนาคต](#14-การขยายระบบในอนาคต)

---

## 1. ภาพรวมสถาปัตยกรรม

### 1.1 System Architecture Diagram

```
                        ┌────────────────────────────────────────────┐
                        │             Web Browser (Client)           │
                        │     index.html (Form)                      │
                        │     result.html (Diagram + BOM)            │
                        └────────────────┬───────────────────────────┘
                                         │ HTTP POST /generate
                                         ▼
                        ┌────────────────────────────────────────────┐
                        │             Flask Web Server               │
                        │                 app.py                     │
                        │    GET /     POST /generate    GET /health │
                        └──────┬──────────────────────────┬──────────┘
                               │                          │
               ┌───────────────▼───────────┐   ┌─────────▼──────────┐
               │       LLM Module          │   │   Diagram Module    │
               │        llm.py             │   │    diagram.py       │
               │                           │   │                     │
               │  Stage 1: parse_req()     │   │  generate_diagram() │
               │  Stage 2: design_topo()   │   │  NetworkX + Matplotlib│
               └───────────┬───────────────┘   └─────────────────────┘
                           │ HTTPS API Call              ▲
                           ▼                             │ topology dict
               ┌───────────────────────┐    ┌───────────┴──────────┐
               │   DeepSeek API        │    │    BOM Module        │
               │  (deepseek-chat)      │    │     bom.py           │
               │  via LangChain OpenAI │    │                      │
               │  compatible SDK       │    │  generate_bom()      │
               └───────────────────────┘    └───────────┬──────────┘
                                                        │
                                            ┌───────────▼──────────┐
                                            │  equipment.json      │
                                            │  (10 device types)   │
                                            └──────────────────────┘
```

### 1.2 Data Flow

```
User Input (Thai/English text)
    │
    ▼
[Stage 1 — LLM Parse]
    │  prompts.py: STAGE1_SYSTEM + STAGE1_USER
    │  DeepSeek API call
    ▼
parsed_params (JSON dict)
    │  org type, num_users, services, security_level, etc.
    │
    ▼
[Stage 2 — LLM Design]
    │  prompts.py: STAGE2_SYSTEM + STAGE2_USER
    │  DeepSeek API call
    ▼
topology (JSON dict)
    │  nodes[], links[], subnets[], notes
    │
    ├──► [Diagram Generator] → base64 PNG string
    │    diagram.py: NetworkX + Matplotlib
    │
    └──► [BOM Generator] → {"items": [...], "total_thb": int}
         bom.py: lookup from equipment.json
    │
    ▼
render_template("result.html", topology, diagram_b64, bom, parsed_params)
```

---

## 2. โครงสร้างไฟล์

```
topogen/
├── app.py              # Flask application — routes และ pipeline orchestration
├── llm.py              # LangChain + DeepSeek API integration (two-stage)
├── prompts.py          # System prompts และ user prompt templates
├── diagram.py          # NetworkX + Matplotlib diagram generator
├── bom.py              # Bill of Materials generator
├── equipment.json      # ฐานข้อมูลอุปกรณ์ (10 รายการ)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (ไม่ commit)
├── .gitignore          # Git ignore rules
├── static/
│   └── style.css       # Frontend CSS
├── templates/
│   ├── index.html      # หน้า Input form
│   └── result.html     # หน้าแสดงผลลัพธ์
└── venv/               # Python virtual environment (ไม่ commit)
```

---

## 3. Technology Stack และ Dependencies

### 3.1 Runtime Dependencies (`requirements.txt`)

| Package | เวอร์ชัน | หน้าที่ |
|---------|---------|--------|
| `flask` | latest | Web framework, routing, template rendering |
| `langchain` | 0.2.17 | LLM abstraction layer, message schema |
| `langchain-openai` | 0.1.25 | OpenAI-compatible client (ใช้กับ DeepSeek) |
| `networkx` | latest | Graph data structure สำหรับ topology |
| `matplotlib` | latest | Render แผนภาพเป็น PNG |
| `python-dotenv` | latest | โหลด environment variables จาก .env |

### 3.2 External Services

| Service | Provider | ใช้สำหรับ |
|---------|---------|----------|
| DeepSeek Chat API | DeepSeek | LLM สำหรับ parse requirements และ design topology |
| Base URL | `https://api.deepseek.com` | Endpoint ของ API |
| Model | `deepseek-chat` (DeepSeek V3) | สามารถเปลี่ยนผ่าน env var ได้ |

### 3.3 Python Version

Python 3.8+ (แนะนำ 3.10 หรือใหม่กว่า)

---

## 4. การติดตั้งระบบ

### 4.1 Prerequisites

```bash
# ตรวจสอบ Python version
python3 --version   # ต้องเป็น 3.8+

# ตรวจสอบ pip
pip3 --version
```

### 4.2 Setup ขั้นตอนทั้งหมด

```bash
# 1. Clone หรือ copy โปรเจกต์
cd /path/to/your/workspace
# copy topogen/ folder มาวาง

# 2. สร้าง virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate      # Linux / macOS
# หรือ
venv\Scripts\activate         # Windows

# 4. ติดตั้ง dependencies
pip install -r requirements.txt

# 5. ตั้งค่า environment variables
cp .env .env.example   # สำรองไว้ (optional)
nano .env              # แก้ไขใส่ API key จริง

# 6. ทดสอบ LLM pipeline
python llm.py

# 7. รัน server
python app.py
# หรือ
flask run
```

### 4.3 การรันบน Production (ตัวอย่าง Gunicorn)

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

> **หมายเหตุ:** Flask debug mode ไม่เหมาะสำหรับ production เนื่องจาก security risk

---

## 5. การตั้งค่า Environment Variables

ไฟล์ `.env` ที่ root ของ project:

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

| Variable | Required | Default | คำอธิบาย |
|----------|----------|---------|----------|
| `DEEPSEEK_API_KEY` | **Yes** | — | API Key จาก platform.deepseek.com |
| `DEEPSEEK_BASE_URL` | No | `https://api.deepseek.com` | Base URL สำหรับ API |
| `DEEPSEEK_MODEL` | No | `deepseek-chat` | Model name ที่ต้องการใช้ |

> **Security:** ห้าม commit `.env` ขึ้น version control `.gitignore` ได้ตั้งค่าไว้แล้ว

---

## 6. การทำงานของแต่ละ Module

### 6.1 `app.py` — Flask Application

**Routes:**

| Method | Path | Handler | คำอธิบาย |
|--------|------|---------|----------|
| GET | `/` | `index()` | Render `index.html` |
| POST | `/generate` | `generate()` | รับ form data, รัน pipeline, render `result.html` |
| GET | `/health` | `health()` | Return `{"status": "ok"}` สำหรับ health check |

**Custom Jinja2 Filter:**
```python
@app.template_filter("thousands")
def thousands_filter(value):
    return "{:,}".format(int(value))
```
ใช้ใน template ด้วย `{{ value | thousands }}` เพื่อแสดงตัวเลขแบบมี comma เช่น `85,000`

**Pipeline ใน `/generate`:**
```python
parsed_params = parse_requirements(user_input)   # Stage 1
topology      = design_topology(parsed_params)    # Stage 2
diagram_b64   = generate_diagram(topology)        # Diagram
bom           = generate_bom(topology)            # BOM
```
Error handling ครอบทั้ง pipeline ด้วย `try/except` เดียว — ถ้า error ใดๆ เกิดขึ้น จะ render `result.html` พร้อม `error=str(e)`

### 6.2 `llm.py` — LLM Integration

**Client initialization (Lazy Singleton):**
```python
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=0.3,   # ต่ำ = deterministic output
            max_tokens=4096,
        )
    return _client
```
ใช้ `ChatOpenAI` จาก `langchain-openai` เพราะ DeepSeek ใช้ OpenAI-compatible API

**JSON Parsing (`_parse_json_response`):**
```python
def _parse_json_response(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
```
strip markdown fences ที่ LLM อาจ return มา แม้จะบอกให้ไม่ใส่ก็ตาม

### 6.3 `prompts.py` — Prompt Templates

แยก prompt ออกจาก business logic เพื่อให้ tune ได้ง่าย มี 4 constants:

- `STAGE1_SYSTEM` — System prompt สำหรับ parse requirements
- `STAGE1_USER` — User prompt template (มี `{user_input}` placeholder)
- `STAGE2_SYSTEM` — System prompt สำหรับ design topology (มี JSON schema และ design rules)
- `STAGE2_USER` — User prompt template (มี `{parsed_params_json}` placeholder)

### 6.4 `diagram.py` — Diagram Generator

**Visual Configuration:**

```python
NODE_STYLE = {
    "cloud":        {"color": "#87CEEB", "marker": "s", "size": 1200},
    "firewall":     {"color": "#FF6B6B", "marker": "D", "size": 1000},
    "router":       {"color": "#4ECDC4", "marker": "o", "size": 1000},
    "switch":       {"color": "#45B7D1", "marker": "s", "size": 800},
    "server":       {"color": "#96CEB4", "marker": "^", "size": 900},
    "access_point": {"color": "#FFEAA7", "marker": "v", "size": 700},
    "pc":           {"color": "#DDA0DD", "marker": "o", "size": 500},
    "printer":      {"color": "#D3D3D3", "marker": "s", "size": 500},
}

LINK_STYLE = {
    "fiber":    {"color": "#FF6B6B", "style": "solid",  "width": 2.5},
    "ethernet": {"color": "#333333", "style": "solid",  "width": 1.5},
    "wireless": {"color": "#999999", "style": "dashed", "width": 1.0},
}

LAYER_Y = {"core": 3, "distribution": 2, "access": 1, "endpoint": 0}
```

**Layout Algorithm (`_compute_positions`):**
1. จัดกลุ่ม nodes ตาม `layer`
2. กำหนด Y coordinate ตาม `LAYER_Y` (core=3 บนสุด, endpoint=0 ล่างสุด)
3. กระจาย nodes แนวนอนใน layer เดียวกัน โดย spacing = 2.5 units

**Output:**
ใช้ `matplotlib.use("Agg")` สำหรับ headless rendering (ไม่ต้องมี display) บันทึกเป็น PNG ใน `BytesIO` แล้ว encode เป็น base64 string

### 6.5 `bom.py` — Bill of Materials Generator

**Logic:**
1. โหลด `equipment.json` ครั้งเดียวใน module-level (`_EQUIPMENT_DB`)
2. วน loop ผ่าน `topology["nodes"]` นับ `model_hint` ที่ซ้ำกัน
3. Lookup ราคาและ spec จาก DB
4. ถ้า `model_hint` ไม่อยู่ใน DB → ใส่ "Unknown" ราคา 0
5. Sort by subtotal descending

**Return value:**
```python
{
    "items": [
        {
            "model_hint": "core_switch",
            "name": "Cisco Catalyst 9300-48T",
            "brand": "Cisco",
            "category": "Switch",
            "specs": "48x GE, 4x 10G SFP+, L3, stackable",
            "qty": 2,
            "unit_price_thb": 85000,
            "subtotal_thb": 170000,
        },
        ...
    ],
    "total_thb": 350000
}
```

---

## 7. LLM Prompt Design

### 7.1 Stage 1 — Parse Requirements

**วัตถุประสงค์:** แปลงภาษาธรรมชาติเป็น structured JSON parameters

**System Prompt หลักการ:**
- บอก LLM ว่าเป็น "network engineer assistant"
- กำหนด output schema ชัดเจน (8 fields)
- บอกให้ใช้ default ที่สมเหตุสมผลเมื่อข้อมูลขาด
- สั่ง `No markdown fences` เพื่อให้ parse ง่าย

**Output schema ที่คาดหวัง:**
```json
{
  "organization_type": "office",
  "num_users": 90,
  "num_locations": 1,
  "area_sqm": null,
  "required_services": ["internet", "file_sharing", "wifi"],
  "security_level": "basic",
  "budget_thb": null,
  "redundancy_needed": false,
  "internet_bandwidth": null,
  "special_requirements": "Server Room 1 ห้อง"
}
```

### 7.2 Stage 2 — Design Topology

**วัตถุประสงค์:** ออกแบบ topology จาก structured parameters

**System Prompt หลักการ:**
- บอก LLM ว่าเป็น "senior network architect"
- ระบุ JSON schema เต็มรูปแบบ (nodes, links, subnets)
- กำหนด `model_hint` เป็น closed enum ที่ match กับ `equipment.json`
- ให้ design rules 8 ข้อ เช่น "ใช้ hierarchical design ถ้า users > 20"
- สั่ง `No markdown fences, no explanation`

**Design Rules (สรุป):**
1. Hierarchical (core→dist→access→endpoint) เมื่อ users > 20
2. Flat star สำหรับ network เล็ก (< 20 users)
3. มี firewall เมื่อ security = "moderate" หรือ "high"
4. Redundant links เมื่อ `redundancy_needed = true`
5. มี access_point เมื่อ "wifi" อยู่ใน services
6. มี "cloud" node สำหรับ ISP/Internet เสมอ
7. Keep minimal — ไม่ over-design
8. Node labels ต้องเป็นภาษาอังกฤษ

### 7.3 Temperature Setting

ใช้ `temperature=0.3` (ต่ำกว่า default ที่ 0.7) เพื่อให้ output deterministic และ follow schema ได้ดีกว่า

---

## 8. Topology JSON Schema

Schema นี้คือ **contract** ระหว่าง LLM output และ Diagram/BOM generator

```json
{
  "topology_name": "Office Network",
  "topology_type": "star | mesh | tree | hybrid",

  "nodes": [
    {
      "id": "router-1",
      "label": "Core Router",
      "type": "router | switch | firewall | server | access_point | pc | printer | cloud",
      "layer": "core | distribution | access | endpoint",
      "specs": {
        "model_hint": "enterprise_router | smb_router | core_switch | access_switch | poe_switch | enterprise_firewall | smb_firewall | rack_server | access_point | ups",
        "ports_needed": 24,
        "bandwidth": "1Gbps"
      }
    }
  ],

  "links": [
    {
      "source": "router-1",
      "target": "switch-core",
      "link_type": "ethernet | fiber | wireless",
      "bandwidth": "1Gbps",
      "label": "Core Link"
    }
  ],

  "subnets": [
    {
      "name": "LAN-Users",
      "cidr": "192.168.1.0/24",
      "vlan_id": 10,
      "node_ids": ["switch-access-1", "ap-1"]
    }
  ],

  "notes": "Design rationale in 2-3 sentences."
}
```

**Field Constraints:**
- `id` — lowercase slug format (e.g., `router-1`, `sw-core`)
- `type` — closed enum (8 values) — ใช้ map สีและ shape ใน diagram
- `layer` — closed enum (4 values) — ใช้กำหนด Y position ใน diagram
- `model_hint` — closed enum (10 values) — ต้อง match key ใน `equipment.json`

---

## 9. Equipment Database

### 9.1 Structure (`equipment.json`)

```json
{
  "<model_hint>": {
    "name": "Full product name",
    "brand": "Manufacturer",
    "category": "Category label",
    "price_thb": 45000,
    "specs": "Key specifications"
  }
}
```

### 9.2 รายการอุปกรณ์ทั้งหมด

| model_hint | ชื่ออุปกรณ์ | ราคา (THB) | หมวดหมู่ |
|-----------|-----------|-----------|---------|
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

### 9.3 การเพิ่มอุปกรณ์ใหม่

แก้ไข `equipment.json` โดยเพิ่ม key ใหม่:
```json
{
  "new_model_hint": {
    "name": "Product Name",
    "brand": "Brand",
    "category": "Category",
    "price_thb": 10000,
    "specs": "Specs description"
  }
}
```

จากนั้นเพิ่ม `new_model_hint` เข้าไปใน `STAGE2_SYSTEM` prompt ในส่วน `model_hint` enum เพื่อให้ LLM รู้จัก

---

## 10. Flask Routes และ Pipeline

### 10.1 GET `/`

```python
@app.route("/")
def index():
    return render_template("index.html")
```

ไม่มี logic เพิ่มเติม render `index.html` โดยตรง

### 10.2 POST `/generate`

```python
@app.route("/generate", methods=["POST"])
def generate():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return render_template("index.html", error="กรุณากรอก requirement")

    try:
        parsed_params = parse_requirements(user_input)
        topology      = design_topology(parsed_params)
        diagram_b64   = generate_diagram(topology)
        bom           = generate_bom(topology)
    except Exception as e:
        return render_template("result.html", error=str(e))

    return render_template("result.html",
        topology=topology,
        diagram_b64=diagram_b64,
        bom=bom,
        parsed_params=parsed_params,
        user_input=user_input,
    )
```

**Template Variables ที่ส่งไป `result.html`:**

| Variable | Type | คำอธิบาย |
|----------|------|----------|
| `topology` | dict | Full topology JSON จาก LLM Stage 2 |
| `diagram_b64` | str | Base64-encoded PNG string |
| `bom` | dict | `{"items": [...], "total_thb": int}` |
| `parsed_params` | dict | Structured parameters จาก LLM Stage 1 |
| `user_input` | str | Raw input จากผู้ใช้ |
| `error` | str | Error message (ถ้า exception เกิดขึ้น) |

### 10.3 GET `/health`

```python
@app.route("/health")
def health():
    return jsonify({"status": "ok"})
```

ใช้สำหรับ load balancer health check หรือ monitoring

---

## 11. Diagram Generation

### 11.1 ขั้นตอนการทำงาน

```
topology dict
    │
    ▼ 1. สร้าง NetworkX Graph
    │   G = nx.Graph()
    │   เพิ่ม nodes ทั้งหมด
    │   เพิ่ม edges (filter invalid links)
    │
    ▼ 2. คำนวณ positions
    │   _compute_positions(nodes)
    │   → group by layer → assign Y
    │   → spread evenly on X axis (spacing=2.5)
    │
    ▼ 3. สร้าง figure
    │   width = max(10, len(nodes) * 1.5)
    │   fig, ax = plt.subplots(figsize=(width, 8))
    │
    ▼ 4. วาด nodes แยกตาม type
    │   nx.draw_networkx_nodes() per type group
    │
    ▼ 5. วาด edges แยกตาม link_type
    │   nx.draw_networkx_edges() per link type group
    │
    ▼ 6. Label nodes + edge bandwidth
    │   nx.draw_networkx_labels()
    │   nx.draw_networkx_edge_labels()
    │
    ▼ 7. Legend + Title
    │
    ▼ 8. Save to BytesIO → base64 encode
```

### 11.2 หมายเหตุสำคัญ

- `matplotlib.use("Agg")` ต้องเรียกก่อน import `pyplot` เพื่อใช้ headless backend
- `plt.close(fig)` หลัง save ทุกครั้ง เพื่อป้องกัน memory leak
- Figure size ปรับ dynamic ตามจำนวน nodes

---

## 12. การทดสอบ

### 12.1 ทดสอบแต่ละ Module แยก

```bash
# ทดสอบ LLM pipeline (Stage 1 + Stage 2)
venv/bin/python llm.py
# ผลที่คาดหวัง: JSON 2 ชุด ไม่มี error

# ทดสอบ Diagram generator
venv/bin/python diagram.py
# ผลที่คาดหวัง: "Saved test_diagram.png"
# ตรวจสอบไฟล์ test_diagram.png

# ทดสอบ BOM generator
venv/bin/python bom.py
# ผลที่คาดหวัง: ตารางราคา + ยอดรวม
```

### 12.2 ทดสอบ Flask Health Check

```bash
venv/bin/python app.py &
curl http://localhost:5000/health
# ผลที่คาดหวัง: {"status": "ok"}
```

### 12.3 ทดสอบ End-to-End ผ่าน curl

```bash
curl -X POST http://localhost:5000/generate \
  -d "user_input=small office 10 users need wifi" \
  -o result.html

# ตรวจสอบ
grep "data:image/png" result.html   # ต้องมี diagram
grep "Bill of Materials" result.html # ต้องมี BOM
```

### 12.4 Test Cases แนะนำ

| Test Case | Input | สิ่งที่ตรวจ |
|-----------|-------|-----------|
| Small network | "home 5 users, wifi" | topology_type=star, ไม่มี firewall |
| Medium office | "office 50 users, 3 floors, wifi, moderate security" | มี firewall, hierarchical layout |
| High security | "bank, 20 users, high security, redundancy" | มี firewall + redundant links |
| Thai language | "ออฟฟิศ 100 คน ต้องการ WiFi" | parse ถูกต้อง |
| Missing info | "network for my company" | ใช้ default values |

---

## 13. การดูแลรักษาและแก้ไขปัญหา

### 13.1 ปัญหาที่พบบ่อย

**1. LLM return JSON ไม่ถูก format**

อาการ: `json.JSONDecodeError` ใน `_parse_json_response()`

สาเหตุ: LLM บางครั้ง wrap JSON ด้วย markdown fences หรือเพิ่ม commentary

แก้ไข: `_parse_json_response()` ใน `llm.py` มี regex strip fences แล้ว ถ้ายังเกิด ให้ดู raw response และเพิ่ม strip pattern

**2. Diagram ดูรกมากเมื่อ node เยอะ**

สาเหตุ: Node ชนกัน label ซ้อนกัน

แก้ไข: เพิ่ม spacing ใน `_compute_positions()` จาก `2.5` เป็นค่าสูงกว่า หรือเพิ่ม `width` multiplier

**3. model_hint ไม่อยู่ใน equipment.json**

อาการ: BOM แสดง "Unknown (xyz)" ราคา 0

สาเหตุ: LLM สร้าง model_hint ที่ไม่อยู่ใน prompt's closed enum

แก้ไข: ตรวจสอบ STAGE2_SYSTEM ว่า list model_hint ครบหรือไม่

**4. Port 5000 ถูกใช้งานอยู่แล้ว**

```bash
lsof -ti:5000 | xargs kill -9
# แล้ว restart Flask
```

**5. `bom.items` ใน Jinja2 ดึง dict method แทน key**

อาการ: `TypeError: 'builtin_function_or_method' object is not iterable`

สาเหตุ: `bom.items` ใน Jinja2 resolves เป็น `dict.items()` method ไม่ใช่ key "items"

แก้ไข (ใช้แล้ว): ใช้ `bom['items']` แทน `bom.items` ใน template

### 13.2 Logging

Flask debug mode จะแสดง traceback เต็มใน terminal และ browser

สำหรับ production ควรเพิ่ม logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
app.logger.info("Processing request for user: %s", user_input[:50])
```

### 13.3 การอัปเดต API Key

แก้ไข `.env`:
```
DEEPSEEK_API_KEY=sk-new-key-here
```
แล้ว restart Flask server (LangChain client โหลด key ที่ startup)

---

## 14. การขยายระบบในอนาคต

### 14.1 Features ที่สามารถเพิ่มได้

| Feature | วิธีทำ |
|---------|--------|
| Export PNG/PDF | เพิ่ม route `/export/<format>` decode base64 แล้ว return file |
| Export JSON | เพิ่มปุ่มในหน้า result ที่ download `topology` JSON |
| Save history | เพิ่ม SQLite + Flask-SQLAlchemy บันทึกทุก generate |
| Config generation | Stage 3: ส่ง topology ให้ LLM สร้าง Cisco/Mikrotik CLI commands |
| Real-time prices | Scrape ราคาจากเว็บ vendor หรือใช้ LLM web search |
| Multiple topology options | Generate 3 options (budget/mid/enterprise) แล้วให้ผู้ใช้เลือก |
| Streaming response | ใช้ `stream=True` ใน LangChain แล้ว SSE ไปที่ browser |

### 14.2 การเปลี่ยน LLM Provider

เนื่องจากใช้ `langchain-openai` ที่ OpenAI-compatible เปลี่ยน provider ได้ง่ายโดยแก้เฉพาะ `.env`:

```env
# เปลี่ยนเป็น OpenAI
DEEPSEEK_API_KEY=sk-openai-key
DEEPSEEK_BASE_URL=https://api.openai.com/v1
DEEPSEEK_MODEL=gpt-4o

# เปลี่ยนเป็น Groq
DEEPSEEK_API_KEY=gsk_groq-key
DEEPSEEK_BASE_URL=https://api.groq.com/openai/v1
DEEPSEEK_MODEL=llama-3.3-70b-versatile
```

---

## Appendix A: Node Type Reference

| type | สี | รูปร่าง | ย่อ Layer |
|------|----|---------|-----------|
| cloud | #87CEEB (ฟ้าอ่อน) | Square | core |
| firewall | #FF6B6B (แดง) | Diamond | core |
| router | #4ECDC4 (เขียวฟ้า) | Circle | core |
| switch | #45B7D1 (น้ำเงิน) | Square | distribution/access |
| server | #96CEB4 (เขียวอ่อน) | Triangle Up | distribution |
| access_point | #FFEAA7 (เหลือง) | Triangle Down | access |
| pc | #DDA0DD (ม่วง) | Circle | endpoint |
| printer | #D3D3D3 (เทา) | Square | endpoint |

## Appendix B: Layer Y Coordinate Reference

| layer | Y value | ตำแหน่งในภาพ |
|-------|---------|-------------|
| core | 3 | บนสุด |
| distribution | 2 | กลางบน |
| access | 1 | กลางล่าง |
| endpoint | 0 | ล่างสุด |

---

*คู่มือระบบนี้ครอบคลุม AI Network Topology Generator เวอร์ชัน 1.0 (MVP)*
