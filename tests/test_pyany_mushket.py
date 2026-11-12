import pytest
from fastapi.testclient import TestClient
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
sys.path.insert(0, BASE_DIR)
for mod in list(sys.modules.keys()):
    if mod == "web" or mod.startswith("web.") or mod == "bot" or mod.startswith("bot."):
        del sys.modules[mod]

from web.app import app, generate_wax_seal_image, MENU_DATA, TABLES_DATA, GROSCHEN_RATE_RUB, THALER_RATE_RUB, DUCAT_RATE_RUB
from bot.bot import create_tavern_bot, TABLES, generate_wax_seal_image as bot_generate_seal

client = TestClient(app)

def test_currency_conversion_rates():
    assert GROSCHEN_RATE_RUB == 35
    assert THALER_RATE_RUB == 350
    assert DUCAT_RATE_RUB == 3500

    # Test menu item math: 12 Groschen = 420 RUB
    ale = next(item for item in MENU_DATA if item["id"] == "ale")
    assert ale["price_groschen"] * GROSCHEN_RATE_RUB == ale["price_rub"]

    # 8 Thalers = 2800 RUB
    venison = next(item for item in MENU_DATA if item["id"] == "venison")
    assert venison["price_thalers"] * THALER_RATE_RUB == venison["price_rub"]

def test_wax_seal_image_generation():
    png_bytes = generate_wax_seal_image(
        guest_name="Князь Даниэль",
        table_name="Дубовый стол у камина",
        cert_id="TEST-12345"
    )
    assert len(png_bytes) > 1000
    # Check PNG magic bytes
    assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'

def test_api_menu_endpoint():
    res = client.get("/api/tavern/menu")
    assert res.status_code == 200
    data = res.json()
    assert "menu" in data
    assert len(data["menu"]) >= 5
    assert "currency_rates" in data

def test_api_tables_and_bounties():
    tables_res = client.get("/api/tavern/tables")
    assert tables_res.status_code == 200
    assert "hearth" in tables_res.json()["tables"]

    bounties_res = client.get("/api/tavern/bounties")
    assert bounties_res.status_code == 200
    assert len(bounties_res.json()["bounties"]) >= 3

def test_api_reserve_table_success():
    payload = {
        "guest_name": "Боярин Даниэль",
        "table_id": "hearth",
        "guest_count": 4,
        "date": "2026-11-25",
        "time": "19:00",
        "phone": "+79991234567",
        "special_wishes": "Подать медовуху охлажденной"
    }
    res = client.post("/api/tavern/reserve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "granted"
    assert data["certificate_id"].startswith("MUSHKET-")
    assert "@Idrisov_prod" in data["message"]

    # Test downloading certificate image
    cert_res = client.get(f"/api/tavern/certificate/{data['certificate_id']}")
    assert cert_res.status_code == 200
    assert cert_res.headers["content-type"] == "image/png"
    assert len(cert_res.content) > 1000

def test_api_reserve_invalid_table_or_phone():
    # Unknown table
    res1 = client.post("/api/tavern/reserve", json={
        "guest_name": "Гость",
        "table_id": "non_existent_table",
        "guest_count": 2,
        "date": "2026-11-25",
        "time": "19:00",
        "phone": "+79991234567"
    })
    assert res1.status_code == 400

    # Short phone
    res2 = client.post("/api/tavern/reserve", json={
        "guest_name": "Гость",
        "table_id": "hearth",
        "guest_count": 2,
        "date": "2026-11-25",
        "time": "19:00",
        "phone": "123"
    })
    assert res2.status_code == 422

def test_bot_initialization():
    bot, dp = create_tavern_bot()
    assert bot is not None
    assert dp is not None
    assert len(dp.sub_routers) >= 1
    assert "hearth" in TABLES
    assert "cellar" in TABLES
