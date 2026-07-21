import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

TEST_REPO = "https://github.com/octocat/Spoon-Knife"


@pytest_asyncio.fixture
async def client():
    if os.path.exists("dev.db"):
        os.remove("dev.db")
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_import_process_list(client: AsyncClient):
    r = await client.post("/api/repository/import", json={"github_url": TEST_REPO})
    assert r.status_code == 201
    repo = r.json()
    assert repo["owner"] == "octocat" and repo["name"] == "Spoon-Knife"

    r2 = await client.post("/api/repository/process", json={"repository_id": repo["id"]})
    assert r2.status_code == 200
    assert r2.json()["status"] == "ready"
    assert r2.json()["total_files"] == 3

    r3 = await client.get(f"/api/repository/{repo['id']}/files")
    assert r3.status_code == 200
    paths = {f["path"] for f in r3.json()}
    assert paths == {"README.md", "index.html", "styles.css"}


@pytest.mark.asyncio
async def test_duplicate_import_rejected(client: AsyncClient):
    await client.post("/api/repository/import", json={"github_url": TEST_REPO})
    r = await client.post("/api/repository/import", json={"github_url": TEST_REPO})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_non_github_url_rejected(client: AsyncClient):
    r = await client.post("/api/repository/import", json={"github_url": "https://notgithub.com/a/b"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_repo_returns_400(client: AsyncClient):
    r = await client.post("/api/repository/import", json={"github_url": "https://github.com/octocat/xyz-does-not-exist-abc"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_process_unknown_repo_returns_404(client: AsyncClient):
    r = await client.post("/api/repository/process", json={"repository_id": 9999})
    assert r.status_code == 404
