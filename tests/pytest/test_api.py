import pytest
import requests


@pytest.fixture()
def client():
    s = requests.Session()
    yield s


@pytest.fixture(scope="session")
def test_user_client():
    s = requests.Session()
    resp = s.request(
        method="post",
        url="http://127.0.0.1:5003",
        json={
            "username": "zfw",
            "password": "zfw520",
        },
    )
    assert resp.status_code == 200


def test_login(client):
    resp = client.request(method="post", url="http://127.0.0.1:5003", json={...})
    assert resp.status_code == 200
