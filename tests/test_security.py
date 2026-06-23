import jwt

from app.core.config import Settings
from app.core.security import decode_access_token


def test_decode_access_token_accepts_user_service_jwt():
    settings = Settings(jwt_secret="shared-secret")
    token = jwt.encode({"id": "user-123", "role": "applicant"}, "shared-secret", algorithm="HS256")

    payload = decode_access_token(token, settings)

    assert payload["id"] == "user-123"
    assert payload["role"] == "applicant"
