import pytest


# --------------------
# CREATE MAIL
# --------------------

def test_create_mail(client):
    response = client.post("/mails", json={
        "sender": "test@mail.com",
        "recipient": "user@mail.com",
        "subject": "hello",
        "body": "world",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["sender"] == "test@mail.com"
    assert data["recipient"] == "user@mail.com"
    assert data["subject"] == "hello"
    assert data["status"] == "sent"
    assert data["reply_to_id"] is None


def test_create_mail_missing_required_fields_returns_422(client):
    response = client.post("/mails", json={"sender": "test@mail.com"})
    assert response.status_code == 422


def test_create_mail_invalid_email_returns_422(client):
    response = client.post("/mails", json={
        "sender": "not-an-email",
        "recipient": "user@mail.com",
    })
    assert response.status_code == 422


# --------------------
# REPLY
# --------------------

def test_create_reply_stores_reply_to_id(client):
    original = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Hello",
        "body": "Original message",
    })
    assert original.status_code == 201
    original_id = original.json()["id"]

    reply = client.post("/mails", json={
        "sender": "b@mail.com",
        "recipient": "a@mail.com",
        "subject": "Re: Hello",
        "body": "Reply message",
        "reply_to_id": original_id,
    })
    assert reply.status_code == 201
    data = reply.json()
    assert data["reply_to_id"] == original_id
    assert data["subject"] == "Re: Hello"
    assert data["sender"] == "b@mail.com"
    assert data["recipient"] == "a@mail.com"


def test_reply_to_nonexistent_mail_still_stores(client):
    """reply_to_id is not FK-validated — service stores it as-is."""
    reply = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Re: Ghost",
        "body": "Replying to phantom",
        "reply_to_id": 999999,
    })
    assert reply.status_code == 201
    assert reply.json()["reply_to_id"] == 999999


def test_reply_chain(client):
    """A reply to a reply (two levels deep) stores the correct reply_to_id."""
    m1 = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Thread start",
        "body": "First message",
    })
    m1_id = m1.json()["id"]

    m2 = client.post("/mails", json={
        "sender": "b@mail.com",
        "recipient": "a@mail.com",
        "subject": "Re: Thread start",
        "body": "Second message",
        "reply_to_id": m1_id,
    })
    m2_id = m2.json()["id"]
    assert m2.json()["reply_to_id"] == m1_id

    m3 = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Re: Thread start",
        "body": "Third message",
        "reply_to_id": m2_id,
    })
    assert m3.status_code == 201
    assert m3.json()["reply_to_id"] == m2_id


# --------------------
# GET MAIL
# --------------------

def test_get_mail(client):
    create = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
    })
    mail_id = create.json()["id"]

    response = client.get(f"/mails/{mail_id}")
    assert response.status_code == 200
    assert response.json()["id"] == mail_id


def test_get_mail_returns_reply_to_id(client):
    original = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Original",
        "body": "Body",
    })
    original_id = original.json()["id"]

    reply = client.post("/mails", json={
        "sender": "b@mail.com",
        "recipient": "a@mail.com",
        "subject": "Re: Original",
        "body": "Reply body",
        "reply_to_id": original_id,
    })
    reply_id = reply.json()["id"]

    fetched = client.get(f"/mails/{reply_id}")
    assert fetched.status_code == 200
    assert fetched.json()["reply_to_id"] == original_id


def test_get_nonexistent_mail_returns_404(client):
    response = client.get("/mails/999999")
    assert response.status_code == 404


# --------------------
# LIST MAILS
# --------------------

def test_list_inbox(client):
    client.post("/mails", json={
        "sender": "sender@mail.com",
        "recipient": "inbox@mail.com",
        "subject": "Inbox test",
        "body": "test",
    })
    response = client.get("/mails", params={"email": "inbox@mail.com", "box": "inbox"})
    assert response.status_code == 200
    mails = response.json()
    assert isinstance(mails, list)
    assert all(m["recipient"] == "inbox@mail.com" for m in mails)


def test_list_sent(client):
    client.post("/mails", json={
        "sender": "sent@mail.com",
        "recipient": "other@mail.com",
        "subject": "Sent test",
        "body": "test",
    })
    response = client.get("/mails", params={"email": "sent@mail.com", "box": "sent"})
    assert response.status_code == 200
    mails = response.json()
    assert isinstance(mails, list)
    assert all(m["sender"] == "sent@mail.com" for m in mails)


def test_list_all(client):
    client.post("/mails", json={
        "sender": "all@mail.com",
        "recipient": "other@mail.com",
        "subject": "All test",
        "body": "test",
    })
    response = client.get("/mails", params={"email": "all@mail.com", "box": "all"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_mails_each_has_reply_to_id_field(client):
    client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
        "subject": "Field check",
        "body": "test",
    })
    response = client.get("/mails", params={"email": "a@mail.com", "box": "sent"})
    assert response.status_code == 200
    for mail in response.json():
        assert "reply_to_id" in mail


def test_search_by_subject(client):
    client.post("/mails", json={
        "sender": "search@mail.com",
        "recipient": "other@mail.com",
        "subject": "UniqueSubject123",
        "body": "test body",
    })
    response = client.get("/mails", params={
        "email": "search@mail.com",
        "box": "sent",
        "search": "UniqueSubject123",
    })
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all("UniqueSubject123" in m["subject"] for m in results)


def test_search_by_body(client):
    client.post("/mails", json={
        "sender": "search@mail.com",
        "recipient": "other@mail.com",
        "subject": "Subject",
        "body": "UniqueBody456",
    })
    response = client.get("/mails", params={
        "email": "search@mail.com",
        "box": "sent",
        "search": "UniqueBody456",
    })
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all("UniqueBody456" in m["body"] for m in results)


# --------------------
# DELETE MAIL
# --------------------

def test_delete_mail(client):
    create = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com",
    })
    mail_id = create.json()["id"]

    response = client.delete(f"/mails/{mail_id}?email=a@mail.com")
    assert response.status_code == 200

    get = client.get(f"/mails/{mail_id}")
    assert get.status_code == 404


def test_delete_others_mail_returns_404(client):
    create = client.post("/mails", json={
        "sender": "owner@mail.com",
        "recipient": "other@mail.com",
    })
    mail_id = create.json()["id"]

    response = client.delete(f"/mails/{mail_id}?email=other@mail.com")
    assert response.status_code == 404


def test_delete_nonexistent_mail_returns_404(client):
    response = client.delete("/mails/999999?email=a@mail.com")
    assert response.status_code == 404
