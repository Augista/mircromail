def test_create_mail(client):
    response = client.post("/mails", json={
        "sender": "test@mail.com",
        "recipient": "user@mail.com",
        "subject": "hello",
        "body": "world"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["sender"] == "test@mail.com"
    assert data["status"] == "sent"


def test_get_mail(client):
    create = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com"
    })

    mail_id = create.json()["id"]

    response = client.get(f"/mails/{mail_id}")

    assert response.status_code == 200
    assert response.json()["id"] == mail_id


def test_delete_mail(client):
    create = client.post("/mails", json={
        "sender": "a@mail.com",
        "recipient": "b@mail.com"
    })

    mail_id = create.json()["id"]

    response = client.delete(f"/mails/{mail_id}?email=a@mail.com")
    assert response.status_code == 200

    get = client.get(f"/mails/{mail_id}")
    assert get.status_code == 404