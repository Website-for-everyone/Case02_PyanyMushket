import os
import io
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Tavern Pyany Mushket API", version="1.0.0")

# Medieval Currency Exchange: 1 Groschen = 35 RUB, 1 Thaler = 350 RUB, 1 Ducat = 3500 RUB
GROSCHEN_RATE_RUB = 35
THALER_RATE_RUB = 350
DUCAT_RATE_RUB = 3500

MENU_DATA = [
    {
        "id": "boar",
        "name": "Запеченный вепрь с брусничным взваром",
        "category": "Горячие яства",
        "price_ducats": 1,
        "price_thalers": 2,
        "price_groschen": 0,
        "price_rub": 4200,
        "desc": "Мякоть дикого вепря, томленая 8 часов в глиняной печи с лесными травами и можжевеловыми ягодами."
    },
    {
        "id": "venison",
        "name": "Оленина в горшочке с кореньями",
        "category": "Горячие яства",
        "price_ducats": 0,
        "price_thalers": 8,
        "price_groschen": 0,
        "price_rub": 2800,
        "desc": "Нежное мясо северного оленя с пастернаком, репой и густым мясным соком."
    },
    {
        "id": "pheasant",
        "name": "Копченый фазан с шафраном",
        "category": "Горячие яства",
        "price_ducats": 0,
        "price_thalers": 6,
        "price_groschen": 0,
        "price_rub": 2100,
        "desc": "Птица горячего ольхового копчения, подается с мочеными антоновскими яблоками."
    },
    {
        "id": "ale",
        "name": "Кружка монастырского темного эля",
        "category": "Хмельные напитки",
        "price_ducats": 0,
        "price_thalers": 0,
        "price_groschen": 12,
        "price_rub": 420,
        "desc": "Густой эль тройного брожения с карамельными и ржаными нотами из монастырской пивоварни."
    },
    {
        "id": "mead",
        "name": "Кубок ставленый медовухи",
        "category": "Хмельные напитки",
        "price_ducats": 0,
        "price_thalers": 0,
        "price_groschen": 18,
        "price_rub": 630,
        "desc": "Старинная хмельная медовуха трехлетней выдержки с добавлением чабреца и корицы."
    },
    {
        "id": "bread",
        "name": "Хлебный каравай с чесночным маслом",
        "category": "Закуски трактира",
        "price_ducats": 0,
        "price_thalers": 0,
        "price_groschen": 8,
        "price_rub": 280,
        "desc": "Пышный подовый хлеб прямо из печи со сбитым маслом и солью."
    }
]

TABLES_DATA = {
    "hearth": {"name": "Дубовый стол у камина", "capacity": "до 4 гостей", "desc": "Жаркое пламя, треск сухих поленьев и лучший вид на лютниста."},
    "standard": {"name": "Стол под королевским штандартом", "capacity": "до 6 гостей", "desc": "Широкая дубовая столешница, тяжелые резные стулья, атмосфера рыцарского пира."},
    "cellar": {"name": "Уединенный винный погреб", "capacity": "до 8 гостей (VIP)", "desc": "Скрыт за кованой решеткой среди дубовых бочек со старинным элем."}
}

BOUNTY_NOTICES = [
    {
        "id": "bounty_1",
        "title": "УКАЗ ЕГО ВЕЛИЧЕСТВА: Черный Барон",
        "reward": "500 ЗОЛОТЫХ ДУКАТОВ",
        "status": "В РОЗЫСКЕ ЖИВЫМ ИЛИ МЕРТВЫМ",
        "body": "Особливые приметы: шрам через левое око, носит бархатный плащ цвета воронова крыла. Замечен на тракте близ Дортмунда."
    },
    {
        "id": "bounty_2",
        "title": "ПОХВАЛЬНАЯ ГРАМОТА ТРАКТИРУ",
        "reward": "ГЕРБОВАЯ ПЕЧАТЬ КОРОНЫ",
        "status": "ПОДТВЕРЖДЕНО КАНЦЛЕРОМ",
        "body": "Сим подтверждается, что медовуха и печеный вепрь в сем заведении подаются по высшему стандарту королевского двора лета 1584."
    },
    {
        "id": "bounty_3",
        "title": "РОЗЫСК: Беглый Алхимик Магнус",
        "reward": "300 ТАЛЕРОВ СЕРЕБРОМ",
        "status": "ОПАСЕН И ВООРУЖЕН СЕЛИТРОЙ",
        "body": "Похитил из башни архиепископа старинный гримуар. Остерегайтесь дымных взрывов и ядовитых паров."
    }
]

RESERVATIONS_DB = []

class ReserveRequest(BaseModel):
    guest_name: str = Field(..., min_length=2)
    table_id: str = Field(..., description="hearth, standard, or cellar")
    guest_count: int = Field(2, ge=1, le=12)
    date: str
    time: str
    phone: str = Field(..., min_length=10)
    special_wishes: Optional[str] = ""

class ReserveResponse(BaseModel):
    status: str
    certificate_id: str
    message: str
    details: dict

def generate_wax_seal_image(guest_name: str, table_name: str, cert_id: str) -> bytes:
    # 600x400 medieval parchment certificate with wax seal
    img = Image.new("RGB", (650, 420), color="#E2D1B3")
    draw = ImageDraw.Draw(img)

    # Burnt edges border
    draw.rectangle([10, 10, 640, 410], outline="#3E2718", width=5)
    draw.rectangle([18, 18, 632, 402], outline="#8B5A2B", width=2)
    draw.rectangle([22, 22, 628, 398], outline="#C89B3C", width=1)

    # Decorative header
    draw.text((325, 45), "ГРАМОТА НА ВХОДЪ И ТРАПЕЗУ", fill="#1F140E", anchor="mm")
    draw.text((325, 75), "ТАВЕРНА «ПЬЯНЫЙ МУШКЕТЪ» ЛѢТА 1584", fill="#8B1E1E", anchor="mm")
    draw.line([(80, 95), (570, 95)], fill="#3E2718", width=2)

    # Certificate body
    body_text = (
        f"Симъ подлинно утверждается, что бояринъ (господинъ)\n"
        f"«{guest_name}»\n"
        f"со товарищи изволилъ занять въ трактире нашемъ:\n"
        f"«{table_name}»\n"
        f"на великую вечерю и вкушеніе хмельныхъ напитковъ."
    )
    draw.text((325, 175), body_text, fill="#2A1B0E", anchor="mm", align="center")

    # Wax seal circle on bottom right
    seal_center = (520, 310)
    seal_radius = 50
    # Outer dark wax
    draw.ellipse([seal_center[0]-seal_radius, seal_center[1]-seal_radius,
                  seal_center[0]+seal_radius, seal_center[1]+seal_radius],
                 fill="#8B1E1E", outline="#590D22", width=3)
    # Inner gold imprint
    draw.ellipse([seal_center[0]-seal_radius+8, seal_center[1]-seal_radius+8,
                  seal_center[0]+seal_radius-8, seal_center[1]+seal_radius-8],
                 outline="#FFD700", width=2)
    draw.text(seal_center, "ПМ\n1584", fill="#FFE5A3", anchor="mm", align="center")

    # Bottom left signature
    draw.text((80, 310), f"Печать и соизволеніе Трактирщика\nГрамота № {cert_id}\nУведомленъ: @Idrisov_prod", fill="#3E2718")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@app.get("/api/tavern/menu")
def get_menu():
    return {
        "menu": MENU_DATA,
        "currency_rates": {
            "groschen_rub": GROSCHEN_RATE_RUB,
            "thaler_rub": THALER_RATE_RUB,
            "ducat_rub": DUCAT_RATE_RUB
        }
    }

@app.get("/api/tavern/tables")
def get_tables():
    return {"tables": TABLES_DATA}

@app.get("/api/tavern/bounties")
def get_bounties():
    return {"bounties": BOUNTY_NOTICES}

@app.post("/api/tavern/reserve", response_model=ReserveResponse)
def reserve_table(req: ReserveRequest):
    if req.table_id not in TABLES_DATA:
        raise HTTPException(status_code=400, detail="Неведомый стол выбран!")

    clean_phone = "".join(ch for ch in req.phone if ch.isdigit() or ch == "+")
    if len(clean_phone) < 10:
        raise HTTPException(status_code=422, detail="Номер для весточки должен содержать минимум 10 цифр!")

    cert_id = f"MUSHKET-{uuid.uuid4().hex[:6].upper()}"
    table_info = TABLES_DATA[req.table_id]

    record = {
        "certificate_id": cert_id,
        "guest_name": req.guest_name,
        "table_id": req.table_id,
        "table_name": table_info["name"],
        "guest_count": req.guest_count,
        "date": req.date,
        "time": req.time,
        "phone": clean_phone,
        "wishes": req.special_wishes,
        "forwarded_to": "@Idrisov_prod"
    }

    RESERVATIONS_DB.append(record)

    return ReserveResponse(
        status="granted",
        certificate_id=cert_id,
        message=f"Грамота № {cert_id} скреплена сургучом! Стол «{table_info['name']}» сохранен за вами. Весть передана @Idrisov_prod.",
        details=record
    )

@app.get("/api/tavern/certificate/{cert_id}")
def get_certificate_image(cert_id: str):
    rec = next((r for r in RESERVATIONS_DB if r["certificate_id"] == cert_id), None)
    if not rec:
        guest_name = "Благородный Гость"
        table_name = "Дубовый стол у камина"
    else:
        guest_name = rec["guest_name"]
        table_name = rec["table_name"]

    png_bytes = generate_wax_seal_image(guest_name, table_name, cert_id)
    return Response(content=png_bytes, media_type="image/png")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(CURRENT_DIR, "index.html")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Таверна «Пьяный Мушкет» открыта. Фолиант на реставрации.</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)
