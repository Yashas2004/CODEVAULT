def register_and_login(client, email, password="testpass123"):
    client.post("/users/register", json={"email": email, "password": password})
    res = client.post("/users/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def create_snippet(client, headers, title="Shareable Snippet"):
    res = client.post("/snippets/", json={
        "title": title, "language": "python", "code": "print('share me')", "tags": ""
    }, headers=headers)
    return res.json()["id"]


def test_create_share_link_returns_slug_and_flag(client):
    headers = register_and_login(client, "share_test@example.com")
    snippet_id = create_snippet(client, headers)
    res = client.post(f"/snippets/{snippet_id}/share", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_public"] is True
    assert len(res.json()["share_slug"]) > 10


def test_shared_snippet_is_publicly_readable_without_auth(client):
    headers = register_and_login(client, "share_public@example.com")
    snippet_id = create_snippet(client, headers, title="Public View Test")
    slug = client.post(f"/snippets/{snippet_id}/share", headers=headers).json()["share_slug"]

    res = client.get(f"/public/snippets/{slug}")
    assert res.status_code == 200
    assert res.json()["title"] == "Public View Test"


def test_revoke_share_blocks_public_access(client):
    headers = register_and_login(client, "share_revoke@example.com")
    snippet_id = create_snippet(client, headers)
    slug = client.post(f"/snippets/{snippet_id}/share", headers=headers).json()["share_slug"]

    revoke_res = client.delete(f"/snippets/{snippet_id}/share", headers=headers)
    assert revoke_res.json()["is_public"] is False
    assert client.get(f"/public/snippets/{slug}").status_code == 404


def test_user_cannot_share_others_snippet(client):
    headers_a = register_and_login(client, "share_owner@example.com")
    headers_b = register_and_login(client, "share_attacker@example.com")
    snippet_id = create_snippet(client, headers_a)
    res = client.post(f"/snippets/{snippet_id}/share", headers=headers_b)
    assert res.status_code == 404


def test_nonexistent_slug_returns_404(client):
    assert client.get("/public/snippets/does-not-exist").status_code == 404


def test_duplicate_create_with_same_idempotency_key_returns_same_snippet(client):
    headers = register_and_login(client, "idempotency_test@example.com")
    key = "same-key-123"
    payload = {"title": "Idempotent Snippet", "language": "python", "code": "x = 1", "tags": ""}

    res1 = client.post("/snippets/", json=payload, headers={**headers, "Idempotency-Key": key})
    res2 = client.post("/snippets/", json=payload, headers={**headers, "Idempotency-Key": key})

    assert res1.json()["id"] == res2.json()["id"]
    assert len(client.get("/snippets/", headers=headers).json()["items"]) == 1


def test_different_idempotency_keys_create_separate_snippets(client):
    headers = register_and_login(client, "idempotency_diff@example.com")
    client.post("/snippets/", json={"title": "First", "language": "python", "code": "x=1", "tags": ""},
                headers={**headers, "Idempotency-Key": "key-a"})
    client.post("/snippets/", json={"title": "Second", "language": "python", "code": "x=2", "tags": ""},
                headers={**headers, "Idempotency-Key": "key-b"})
    assert len(client.get("/snippets/", headers=headers).json()["items"]) == 2


def test_rate_limiter_blocks_after_max_requests(client):
    for i in range(5):  # /users/register is limited to 5/min
        client.post("/users/register", json={"email": f"rate_{i}@example.com", "password": "testpass123"})
    res = client.post("/users/register", json={"email": "rate_overflow@example.com", "password": "testpass123"})
    assert res.status_code == 429