def register_and_login(client, email, password="testpass123"):
    client.post("/users/register", json={"email": email, "password": password})
    res = client.post("/users/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_view_count_increments_on_each_public_view(client):
    headers = register_and_login(client, "analytics_test@example.com")
    create_res = client.post("/snippets/", json={
        "title": "Popular Snippet", "language": "python", "code": "x = 1", "tags": ""
    }, headers=headers)
    snippet_id = create_res.json()["id"]
    slug = client.post(f"/snippets/{snippet_id}/share", headers=headers).json()["share_slug"]

    for _ in range(3):
        client.get(f"/public/snippets/{slug}")

    items = client.get("/snippets/", headers=headers).json()["items"]
    viewed = next(s for s in items if s["id"] == snippet_id)
    assert viewed["view_count"] == 3


def test_private_snippet_has_zero_view_count(client):
    headers = register_and_login(client, "analytics_private@example.com")
    client.post("/snippets/", json={
        "title": "Private Snippet", "language": "python", "code": "x = 1", "tags": ""
    }, headers=headers)

    items = client.get("/snippets/", headers=headers).json()["items"]
    assert items[0]["view_count"] == 0