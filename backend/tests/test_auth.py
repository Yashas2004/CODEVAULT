def test_register_new_user(client):
    response = client.post("/users/register", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_register_duplicate_email_fails(client):
    client.post("/users/register", json={
        "email": "dupe@example.com",
        "password": "testpass123"
    })
    response = client.post("/users/register", json={
        "email": "dupe@example.com",
        "password": "differentpass"
    })
    assert response.status_code == 400


def test_login_with_correct_credentials(client):
    client.post("/users/register", json={
        "email": "login@example.com",
        "password": "correctpass"
    })
    response = client.post("/users/login", data={
        "username": "login@example.com",
        "password": "correctpass"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails(client):
    client.post("/users/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpass"
    })
    response = client.post("/users/login", data={
        "username": "wrongpass@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401