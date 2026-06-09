"""
E2E tests for mail flow through the API Gateway.
Requires the full Docker stack to be running (docker-compose up).
"""

import pytest
from conftest import SENDER_EMAIL, RECEIVER_EMAIL, auth_headers


class TestSendMail:
    def test_send_mail_success(self, http, sender_token):
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "E2E Test Mail",
            "body": "Hello from e2e test",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["sender"] == SENDER_EMAIL
        assert body["recipient"] == RECEIVER_EMAIL
        assert body["subject"] == "E2E Test Mail"
        assert body["status"] == "sent"
        assert "id" in body
        assert body["reply_to_id"] is None

    def test_send_mail_no_auth_returns_401(self, http):
        r = http.post("/api/mails", json={
            "recipient": RECEIVER_EMAIL,
            "subject": "No auth",
            "body": "Should fail",
        })
        assert r.status_code == 401

    def test_send_mail_missing_recipient_returns_422(self, http, sender_token):
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "subject": "No recipient",
            "body": "Should fail",
        })
        assert r.status_code == 422


class TestGetMail:
    @pytest.fixture(scope="class")
    def sent_mail(self, http, sender_token):
        """Send one mail and return the response body."""
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "Fixture Mail",
            "body": "Created by fixture",
        })
        assert r.status_code == 201
        return r.json()

    def test_get_mail_by_id(self, http, sender_token, sent_mail):
        mail_id = sent_mail["id"]
        r = http.get(f"/api/mails/{mail_id}", headers=auth_headers(sender_token))
        assert r.status_code == 200
        assert r.json()["id"] == mail_id

    def test_get_mail_response_has_reply_to_id_field(self, http, sender_token, sent_mail):
        mail_id = sent_mail["id"]
        r = http.get(f"/api/mails/{mail_id}", headers=auth_headers(sender_token))
        assert r.status_code == 200
        assert "reply_to_id" in r.json()

    def test_get_nonexistent_mail_returns_404(self, http, sender_token):
        r = http.get("/api/mails/999999", headers=auth_headers(sender_token))
        assert r.status_code == 404

    def test_get_mail_no_auth_returns_401(self, http, sent_mail):
        r = http.get(f"/api/mails/{sent_mail['id']}")
        assert r.status_code == 401


class TestReplyMail:
    @pytest.fixture(scope="class")
    def original_mail(self, http, sender_token):
        """Sender sends an original mail to receiver."""
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "Original Thread",
            "body": "This is the original message.",
        })
        assert r.status_code == 201
        return r.json()

    def test_reply_mail_success(self, http, receiver_token, original_mail):
        original_id = original_mail["id"]
        r = http.post("/api/mails", headers=auth_headers(receiver_token), json={
            "recipient": SENDER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "This is the reply.",
            "reply_to_id": original_id,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["reply_to_id"] == original_id
        assert data["sender"] == RECEIVER_EMAIL
        assert data["recipient"] == SENDER_EMAIL
        assert data["subject"] == "Re: Original Thread"
        assert data["status"] == "sent"

    def test_reply_appears_in_sender_inbox(self, http, sender_token, original_mail):
        """Sender should see the reply in their inbox."""
        original_id = original_mail["id"]
        # Send a fresh reply so we know it's definitely there
        http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": SENDER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "Inbox check reply",
            "reply_to_id": original_id,
        })
        r = http.get("/api/mails", headers=auth_headers(sender_token),
                     params={"box": "inbox"})
        assert r.status_code == 200
        mails = r.json()
        assert any(m["subject"] == "Re: Original Thread" for m in mails)

    def test_reply_no_auth_returns_401(self, http, original_mail):
        r = http.post("/api/mails", json={
            "recipient": SENDER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "Should fail",
            "reply_to_id": original_mail["id"],
        })
        assert r.status_code == 401

    def test_reply_to_id_is_returned_by_get(self, http, sender_token, receiver_token, original_mail):
        original_id = original_mail["id"]
        reply = http.post("/api/mails", headers=auth_headers(receiver_token), json={
            "recipient": SENDER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "Check get endpoint",
            "reply_to_id": original_id,
        })
        reply_id = reply.json()["id"]

        fetched = http.get(f"/api/mails/{reply_id}", headers=auth_headers(sender_token))
        assert fetched.status_code == 200
        assert fetched.json()["reply_to_id"] == original_id

    def test_reply_chain(self, http, sender_token, receiver_token, original_mail):
        """Reply to a reply — verify nested reply_to_id is stored correctly."""
        original_id = original_mail["id"]

        first_reply = http.post("/api/mails", headers=auth_headers(receiver_token), json={
            "recipient": SENDER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "First reply",
            "reply_to_id": original_id,
        })
        assert first_reply.status_code == 201
        first_reply_id = first_reply.json()["id"]

        second_reply = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "Re: Original Thread",
            "body": "Second reply (reply to reply)",
            "reply_to_id": first_reply_id,
        })
        assert second_reply.status_code == 201
        assert second_reply.json()["reply_to_id"] == first_reply_id


class TestInboxAndSent:
    @pytest.fixture(scope="class", autouse=True)
    def send_test_mail(self, http, sender_token):
        """Ensure at least one mail exists before inbox/sent checks."""
        http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "Inbox check",
            "body": "For inbox/sent test",
        })

    def test_sender_sees_mail_in_sent(self, http, sender_token):
        r = http.get("/api/sent", headers=auth_headers(sender_token))
        assert r.status_code == 200
        mails = r.json()
        assert isinstance(mails, list)
        assert any(m["sender"] == SENDER_EMAIL for m in mails)

    def test_receiver_sees_mail_in_inbox(self, http, receiver_token):
        r = http.get("/api/inbox", headers=auth_headers(receiver_token))
        assert r.status_code == 200
        mails = r.json()
        assert isinstance(mails, list)
        assert any(m["recipient"] == RECEIVER_EMAIL for m in mails)

    def test_inbox_no_auth_returns_401(self, http):
        r = http.get("/api/inbox")
        assert r.status_code == 401

    def test_sent_no_auth_returns_401(self, http):
        r = http.get("/api/sent")
        assert r.status_code == 401


class TestListMails:
    def test_list_inbox(self, http, receiver_token):
        r = http.get("/api/mails", headers=auth_headers(receiver_token),
                     params={"box": "inbox"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_sent(self, http, sender_token):
        r = http.get("/api/mails", headers=auth_headers(sender_token),
                     params={"box": "sent"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_all(self, http, sender_token):
        r = http.get("/api/mails", headers=auth_headers(sender_token),
                     params={"box": "all"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_mails_each_has_reply_to_id_field(self, http, sender_token):
        r = http.get("/api/mails", headers=auth_headers(sender_token),
                     params={"box": "sent"})
        assert r.status_code == 200
        for mail in r.json():
            assert "reply_to_id" in mail

    def test_search_by_subject(self, http, sender_token):
        r = http.get("/api/mails", headers=auth_headers(sender_token),
                     params={"box": "sent", "search": "E2E Test Mail"})
        assert r.status_code == 200
        results = r.json()
        assert all("E2E Test Mail" in m["subject"] for m in results)


class TestDeleteMail:
    def test_delete_own_sent_mail(self, http, sender_token):
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "To be deleted",
            "body": "Delete me",
        })
        assert r.status_code == 201
        mail_id = r.json()["id"]

        r2 = http.delete(f"/api/mails/{mail_id}", headers=auth_headers(sender_token))
        assert r2.status_code == 200

        r3 = http.get(f"/api/mails/{mail_id}", headers=auth_headers(sender_token))
        assert r3.status_code == 404

    def test_delete_others_mail_returns_404(self, http, receiver_token, sender_token):
        r = http.post("/api/mails", headers=auth_headers(sender_token), json={
            "recipient": RECEIVER_EMAIL,
            "subject": "Not yours",
            "body": "Receiver cannot delete this",
        })
        assert r.status_code == 201
        mail_id = r.json()["id"]

        r2 = http.delete(f"/api/mails/{mail_id}", headers=auth_headers(receiver_token))
        assert r2.status_code == 404

    def test_delete_no_auth_returns_401(self, http):
        r = http.delete("/api/mails/1")
        assert r.status_code == 401
