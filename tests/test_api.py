import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from asyncio import sleep
import subprocess
from base64 import b64encode
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.sites import get_db
from app.run import app
import logging


### - Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log(text):
    logger.info(text)
    
    
### - Test Database session
SQLALCHEMY_DATABASE_URL = "sqlite:///test_web_monitor.db"
TEST_DB_PATH = "./test_web_monitor.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
    
    
### - Celery worker process
@pytest.fixture(scope="session", autouse=True)
def start_celery_worker():
    worker = subprocess.Popen(
        ["celery", "-A", "app.background_worker", "worker", "--loglevel=info", "-P", "gevent"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    yield worker
    worker.terminate()
    worker.wait()


### - Authentication by HTTP Basic Auth
USERNAME = "pratik"
PASSWORD = "tripathy"

def basic_auth_header(username, password):
    credentials = f"{username}:{password}"
    encoded_credentials = b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


### - Dummy Data
test_site_1 = {
    "url": "https://google.com/",
    "check_interval_seconds": 2,
    "name": "Google Search",
    "expected_status_code": 200
}

test_site_2 = {
    "url": "https://www.wikimedia.org/",
    "check_interval_seconds": 2,
    "name": "WikiMedia",
    "expected_status_code": 200
}

test_webhook_1 = {
    "discord_webhook_url": "https://discord.com/api/webhooks/1338284604985049091/uY-J2H70SpITmGEoPIk-02lzNiI-jqWzM2Zttqf0mXYPm1p7Z6-XVJp4WgggUZepxG91"
}

test_webhook_2 = {
    "discord_webhook_url": "https://discord.com/api/webhooks/1338284988084260884/UFbhG48wu6tiJkMSeEUoyeAuZaQmZHO8B678l7tjtj00m4TPU_6lbokz4CKx4Dq9vGw4"
}

### - Pre Conditions
# Creating a site
@pytest.fixture
def create_site(client):
    headers = basic_auth_header(USERNAME, PASSWORD)
    response = client.post("/sites", json=test_site_1, headers=headers)
    assert response.status_code == 200
    return response.json()

# Creating two sites
@pytest.fixture
def create_multiple_sites(client):
    headers = basic_auth_header(USERNAME, PASSWORD)
    response_1 = client.post("/sites", json=test_site_1, headers=headers)
    response_2 = client.post("/sites", json=test_site_2, headers=headers)
    assert response_1.status_code == 200
    assert response_2.status_code == 200
    return [response_1.json(), response_2.json()]

# Creating a webhook
@pytest.fixture
def create_webhook(client, create_site):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_site_id = create_site["id"]
    test_webhook_1["site_id"] = created_site_id
    response = client.post(f"/webhooks", json=test_webhook_1, headers=headers)
    assert response.status_code == 200
    return response.json()

# Creating one webhook for each site
@pytest.fixture
def create_multiple_webhooks(client, create_multiple_sites):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_site_id_1 = create_multiple_sites[0]["id"]
    created_site_id_2 = create_multiple_sites[1]["id"]
    test_webhook_1["site_id"] = created_site_id_1
    test_webhook_2["site_id"] = created_site_id_2
    response_1 = client.post(f"/webhooks/", json=test_webhook_1, headers=headers)
    response_2 = client.post(f"/webhooks/", json=test_webhook_2, headers=headers)
    assert response_1.status_code == 200
    assert response_2.status_code == 200
    return [response_1.json(), response_2.json()]

### - Tests (10)
# getting one site
def test_get_site_by_id(client, create_site):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_site_id = create_site["id"]
    response = client.get(f"/sites/{created_site_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert (data["url"] == create_site["url"]) and (data["check_interval_seconds"] == create_site["check_interval_seconds"]) and (data["name"] == create_site["name"]) and (data["expected_status_code"] == create_site["expected_status_code"])

# getting all the sites
def test_get_all_sites(client, create_multiple_sites):
    headers = basic_auth_header(USERNAME, PASSWORD)
    response = client.get(f"/sites", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(create_multiple_sites)
    assert all([(item in data) for item in create_multiple_sites])
    
# creating a site
def test_create_site(client):
    headers = basic_auth_header(USERNAME, PASSWORD)
    response_1 = client.post("/sites", json=test_site_1, headers=headers)
    assert response_1.status_code == 200
    data_1 = response_1.json()
    id_1 = data_1["id"]
    response_2 = client.get(f"/sites/{id_1}", headers=headers)
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_1 == data_2
    
# deleting a site
def test_delete_site(client, create_site):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_site_id = create_site["id"]
    response_1 = client.delete(f"/sites/{created_site_id}", headers=headers)
    assert response_1.status_code == 200
    response_2 = client.get(f"/sites/{created_site_id}", headers=headers)
    assert response_2.status_code == 400
    
# getting a webhook
def test_get_webhook_by_id(client, create_webhook):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_webhook_site_id = create_webhook["id"]
    response = client.get(f"/webhooks/{created_webhook_site_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all([(item["discord_webhook_url"] == create_webhook["discord_webhook_url"]) for item in data])
    
# getting all the webhooks
def test_get_webhooks(client, create_multiple_webhooks):
    headers = basic_auth_header(USERNAME, PASSWORD)
    response = client.get(f"/webhooks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all([item in create_multiple_webhooks for item in data])
    
# creating two webhooks of same site
def test_create_webhooks(client, create_site):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_site_id = create_site["id"]
    test_webhook_1["site_id"] = created_site_id
    test_webhook_2["site_id"] = created_site_id
    response_1 = client.post(f"/webhooks", json=test_webhook_1, headers=headers)
    response_2 = client.post(f"/webhooks", json=test_webhook_2, headers=headers)
    assert response_1.status_code == 200
    assert response_2.status_code == 200
    response_3 = client.get(f"/webhooks/{created_site_id}", headers=headers)
    assert response_3.status_code == 200
    data_1 = response_1.json()
    data_2 = response_2.json()
    data_3 = response_3.json()
    assert all([item in [data_1, data_2] for item in data_3])
    
# deleting webhhooks
def test_delete_webhooks(client, create_multiple_webhooks):
    headers = basic_auth_header(USERNAME, PASSWORD)
    created_webhook_id = create_multiple_webhooks[0]["id"]
    created_webhook_site_id = create_multiple_webhooks[0]["site_id"]
    response_1 = client.delete(f"/webhooks/{created_webhook_id}", headers=headers)
    assert response_1.status_code == 200
    response_2 = client.get(f"/webhooks/{created_webhook_site_id}", headers=headers)
    assert response_2.status_code == 200
    data = response_2.json()
    assert create_multiple_webhooks[0] not in data

# test to see whether the monitoring is starting and ending
def test_monitoring_start_end(client):
    headers = basic_auth_header(USERNAME, PASSWORD)
    site_id = 1
    test_webhook_1["site_id"] = site_id
    response_1 = client.post(f"/webhooks", json=test_webhook_1, headers=headers)
    assert response_1.status_code == 200
    response_2 = client.post("/sites", json=test_site_1, headers=headers)
    assert response_2.status_code == 200
    response_3 = client.delete(f"/sites/{site_id}", headers=headers)
    assert response_3.status_code == 200
    
# test to see whether the monitoring is starting, one status check and ending
async def test_monitoring_start_between_end(client, start_celery_worker):
    headers = basic_auth_header(USERNAME, PASSWORD)
    site_id = 1
    test_webhook_1["site_id"] = site_id
    response_1 = client.post(f"/webhooks", json=test_webhook_1, headers=headers)
    assert response_1.status_code == 200
    response_2 = client.post("/sites", json=test_site_1, headers=headers)
    assert response_2.status_code == 200
    await sleep(2)
    response_3 = client.get(f"/sites/{site_id}/history", headers=headers)
    assert response_3.status_code == 200
    data = response_3.json()
    assert data[0]["status"] == "INITIAL"
    response_4 = client.delete(f"/sites/{site_id}", headers=headers)
    assert response_4.status_code == 200