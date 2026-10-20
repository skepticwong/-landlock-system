import unittest
from unittest.mock import patch

from jose import jwt

from app import app
from config import config
from utils.security import create_access_token, decode_token


class DummyUser:
    def __init__(self):
        self.id = 42
        self.full_name = "Jane Doe"
        self.is_superuser = False
        self.is_official = False


class CertificatesEndpointTests(unittest.TestCase):
    @staticmethod
    def _client_with_plots(plot_rows):
        with patch("app.db.select") as mock_select, patch("models.user.User.get_by_id", return_value=DummyUser()):
            mock_select.side_effect = [
                [{"id": 42, "full_name": "Jane Doe", "email": "jane@example.com", "phone": "0999999999", "is_superuser": False, "role": "citizen"}],
                plot_rows,
            ]
            token = create_access_token({"sub": "42"})
            client = app.test_client()
            response = client.get("/api/certificates", headers={"Authorization": f"Bearer {token}"})
            return response

    def test_returns_only_verified_certificates_for_multiple_plots(self):
        response = self._client_with_plots([
            {"id": 1, "user_id": 42, "plot_name": "Plot A", "status": "verified", "created_at": "2025-01-01T08:00:00"},
            {"id": 2, "user_id": 42, "plot_name": "Plot B", "status": "pending", "created_at": "2025-02-01T08:00:00"},
        ])

        self.assertEqual(response.status_code, 200)
        certificates = response.get_json()
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0]["parcelId"], "MLW-1")
        self.assertEqual(certificates[0]["location"], "Plot A")

    def test_returns_all_verified_certificates_for_users_with_multiple_lands(self):
        response = self._client_with_plots([
            {"id": 11, "user_id": 42, "plot_name": "North Plot", "status": "verified", "created_at": "2025-01-01T08:00:00"},
            {"id": 12, "user_id": 42, "plot_name": "South Plot", "status": "approved", "created_at": "2025-02-01T08:00:00"},
        ])

        self.assertEqual(response.status_code, 200)
        certificates = response.get_json()
        self.assertEqual(len(certificates), 2)
        parcel_ids = {certificate["parcelId"] for certificate in certificates}
        self.assertEqual(parcel_ids, {"MLW-11", "MLW-12"})

    def test_accepts_legacy_jwt_secret(self):
        legacy_token = jwt.encode({"sub": "99"}, "landlock-legacy-secret", algorithm=config.JWT_ALGORITHM)
        payload = decode_token(legacy_token)
        self.assertEqual(payload["sub"], "99")


if __name__ == "__main__":
    unittest.main()
