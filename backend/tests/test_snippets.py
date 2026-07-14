def register_and_login(client, email="snippet_test@example.com", password="testpass123"):
    """Helper: registers a user and returns an auth header dict."""
    client.post("/users/register", json={"email": email, "password": password})
    res = client.post("/users/login", data={"username": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_snippet(client):
    headers = register_and_login(client)
    create_res = client.post("/snippets/", json={
        "title": "Test Snippet",
        "language": "python",
        "code": "print('hello')",
        "tags": "test"
    }, headers=headers)
    assert create_res.status_code == 200

    list_res = client.get("/snippets/", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["items"][0]["title"] == "Test Snippet"


def test_cache_invalidates_after_create(client):
    """This is the bug we fixed in Step 1 — verify it stays fixed."""
    headers = register_and_login(client, email="cache_test@example.com")

    # First list call — caches an empty result
    res1 = client.get("/snippets/", headers=headers)
    assert res1.json()["items"] == []

    # Create a snippet
    client.post("/snippets/", json={
        "title": "Cache Test Snippet",
        "language": "python",
        "code": "x = 1",
        "tags": ""
    }, headers=headers)

    # List again — should NOT be the stale cached empty list
    res2 = client.get("/snippets/", headers=headers)
    assert len(res2.json()["items"]) == 1
    assert res2.json()["items"][0]["title"] == "Cache Test Snippet"


def test_pagination_returns_correct_page_size(client):
    headers = register_and_login(client, email="pagination_test@example.com")

    # create 25 snippets
    for i in range(25):
        client.post("/snippets/", json={
            "title": f"Snippet {i}",
            "language": "python",
            "code": f"x = {i}",
            "tags": ""
        }, headers=headers)

    first_page = client.get("/snippets/?limit=20", headers=headers)
    data = first_page.json()
    assert len(data["items"]) == 20
    assert data["has_more"] is True
    assert data["next_cursor"] is not None

    second_page = client.get(f"/snippets/?limit=20&cursor={data['next_cursor']}", headers=headers)
    data2 = second_page.json()
    assert len(data2["items"]) == 5
    assert data2["has_more"] is False
    assert data2["next_cursor"] is None


def test_user_cannot_delete_others_snippet(client):
    """Security test: user A should not be able to delete user B's snippet."""
    headers_a = register_and_login(client, email="user_a@example.com")
    headers_b = register_and_login(client, email="user_b@example.com")

    create_res = client.post("/snippets/", json={
        "title": "User A's snippet",
        "language": "python",
        "code": "secret = True",
        "tags": ""
    }, headers=headers_a)
    snippet_id = create_res.json()["id"]

    delete_res = client.delete(f"/snippets/{snippet_id}", headers=headers_b)
    assert delete_res.status_code == 404  # user B shouldn't even see it exists
    
def test_update_snippet(client):
    headers = register_and_login(client, email="update_test@example.com")
    create_res = client.post("/snippets/", json={
        "title": "Original Title",
        "language": "python",
        "code": "x = 1",
        "tags": ""
    }, headers=headers)
    snippet_id = create_res.json()["id"]

    update_res = client.put(f"/snippets/{snippet_id}", json={
        "title": "Updated Title",
        "language": "python",
        "code": "x = 2",
        "tags": "updated"
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"

    list_res = client.get("/snippets/", headers=headers)
    assert list_res.json()["items"][0]["title"] == "Updated Title"


def test_user_cannot_update_others_snippet(client):
    headers_a = register_and_login(client, email="update_user_a@example.com")
    headers_b = register_and_login(client, email="update_user_b@example.com")

    create_res = client.post("/snippets/", json={
        "title": "User A's snippet",
        "language": "python",
        "code": "secret = True",
        "tags": ""
    }, headers=headers_a)
    snippet_id = create_res.json()["id"]

    update_res = client.put(f"/snippets/{snippet_id}", json={
        "title": "Hacked",
        "language": "python",
        "code": "hacked = True",
        "tags": ""
    }, headers=headers_b)
    assert update_res.status_code == 404