import io
import unittest
from unittest.mock import patch

from app import app
from utils.security import create_access_token


class DummyUser:
    def __init__(self, *, is_superuser=False, identity_status="unverified"):
        self.id = 42
        self.full_name = "Jane Doe"
        self.role = "citizen"
        self.is_superuser = is_superuser
        self.is_official = is_superuser
        self.identity_status = identity_status


class IdentityVerificationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _headers(self):
        token = create_access_token({"sub": "42"})
        return {"Authorization": f"Bearer {token}"}

    @patch("models.user.User.get_by_id", return_value=DummyUser(identity_status="pending"))
    def test_unverified_user_cannot_initiate_sale(self, _get_user):
        response = self.client.post(
            "/api/transactions/sale",
            json={},
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["identity_status"], "pending")

    @patch("models.user.User.get_by_id", return_value=DummyUser(identity_status="unverified"))
    def test_unverified_user_can_still_submit_claims(self, _get_user):
        with patch("app.db.insert") as insert:
            insert.side_effect = [
                {"id": 9, "points": "[]", "plot_name": "Test claim", "status": "pending"},
                {"id": 1},
            ]
            response = self.client.post(
                "/api/plots",
                json={"plot_name": "Test claim", "points": [[34.0, -13.0], [34.1, -13.0], [34.0, -13.1]]},
                headers=self._headers(),
            )

        self.assertEqual(response.status_code, 201)

    @patch("models.user.User.get_by_id", return_value=DummyUser(identity_status="pending"))
    @patch("routes.identity.config.IDENTITY_DOCUMENT_ENCRYPTION_KEY", None)
    def test_id_upload_fails_closed_without_encryption_key(self, _get_user):
        response = self.client.post(
            "/api/user/me/identity-verification",
            data={
                "national_id": "MW-12345",
                "front": (io.BytesIO(b"\xff\xd8\xfffront"), "front.jpg"),
                "back": (io.BytesIO(b"\xff\xd8\xffback"), "back.jpg"),
            },
            headers=self._headers(),
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("encryption", response.get_json()["error"].lower())

    @patch("models.user.User.get_by_id", return_value=DummyUser())
    def test_non_admin_cannot_review_identity(self, _get_user):
        response = self.client.post(
            "/api/admin/identity-verifications/1/review",
            json={"decision": "verified"},
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 403)

    @patch("models.user.User.get_by_id", return_value=DummyUser(is_superuser=True))
    def test_rejection_requires_reason(self, _get_user):
        response = self.client.post(
            "/api/admin/identity-verifications/1/review",
            json={"decision": "rejected", "reason": "  "},
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("reason", response.get_json()["error"].lower())


if __name__ == "__main__":
    unittest.main()
