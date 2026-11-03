import pytest
from httpx import ASGITransport, AsyncClient

from src.web.app import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "providers_available" in data


@pytest.mark.asyncio
async def test_favicon_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        resp = await client.get("/favicon.ico")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_presets_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        resp = await client.get("/api/presets")
        assert resp.status_code == 200
        presets = resp.json()
        assert len(presets) >= 2
        assert "name" in presets[0]


@pytest.mark.asyncio
async def test_generate_endpoint_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        payload = {
            "name": "Тестовый манометр МТИ",
            "manufacturer": "Манотомь",
            "specs": {"класс точности": "0.6", "диапазон": "0-1 МПа"},
            "description": (
                "Прибор для измерения точного давления в трубопроводе."
            ),
        }
        resp = await client.post("/api/generate?provider=mock", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "seo_title" in data
        assert "seo_description" in data
        assert "markdown" in data
        assert "plain_text" in data
        assert len(data["seo_title"]) <= 70


@pytest.mark.asyncio
async def test_generate_endpoint_empty_name_returns_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        payload = {"name": "   ", "manufacturer": "Тест"}
        resp = await client.post("/api/generate", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_endpoint_v1_path():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        payload = {
            "name": "Тестовый манометр МТИ",
            "manufacturer": "Манотомь",
            "specs": {"класс точности": "0.6"},
            "description": "Прибор для измерения давления.",
        }
        resp = await client.post(
            "/api/v1/generate?provider=mock", json=payload
        )
        assert resp.status_code == 200
        assert "seo_title" in resp.json()


@pytest.mark.asyncio
async def test_permission_api_key_check(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-token")
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        payload = {
            "name": "Тестовый датчик",
            "specs": {},
        }
        # Без ключа -> 403 Forbidden
        unauth_resp = await client.post("/api/generate", json=payload)
        assert unauth_resp.status_code == 403

        # С корректным X-API-Key -> 200 OK
        headers = {"X-API-Key": "secret-test-token"}
        auth_resp = await client.post(
            "/api/generate?provider=mock", json=payload, headers=headers
        )
        assert auth_resp.status_code == 200
