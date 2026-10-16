import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from jwcrypto import jwk, jwt
from oauth2_provider.models import Application
from rest_framework import status

from dusken.models import DuskenUser

RSA_PRIVATE_KEY = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    .decode()
)
REDIRECT_URI = "https://client.example.com/callback"


@override_settings(OAUTH2_PROVIDER={**settings.OAUTH2_PROVIDER, "OIDC_RSA_PRIVATE_KEY": RSA_PRIVATE_KEY})
class OAuth2AuthorizationCodeFlowTestCase(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            "olanord", email="olanord@example.com", password="mypassword", first_name="Ola", last_name="Nordmann"
        )
        self.client_secret = "client-secret"  # noqa: S105
        self.application = Application.objects.create(
            name="Test client",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=REDIRECT_URI,
            client_secret=self.client_secret,
            algorithm=Application.RS256_ALGORITHM,
            skip_authorization=True,
        )

    def obtain_tokens(self):
        code_verifier = secrets.token_urlsafe(48)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).rstrip(b"=")

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("oauth2_provider:authorize"),
            {
                "response_type": "code",
                "client_id": self.application.client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "openid profile email",
                "state": "some-state",
                "code_challenge": code_challenge.decode(),
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == status.HTTP_302_FOUND
        redirect = urlparse(response["Location"])
        assert f"{redirect.scheme}://{redirect.netloc}{redirect.path}" == REDIRECT_URI
        params = parse_qs(redirect.query)
        assert params["state"] == ["some-state"]

        self.client.logout()
        response = self.client.post(
            reverse("oauth2_provider:token"),
            {
                "grant_type": "authorization_code",
                "code": params["code"][0],
                "redirect_uri": REDIRECT_URI,
                "client_id": self.application.client_id,
                "client_secret": self.client_secret,
                "code_verifier": code_verifier,
            },
        )
        assert response.status_code == status.HTTP_200_OK, response.content
        return response.json()

    def test_id_token_is_signed_and_has_claims(self):
        tokens = self.obtain_tokens()
        key = jwk.JWK.from_pem(RSA_PRIVATE_KEY.encode())
        claims = jwt.JWT(jwt=tokens["id_token"], key=key, expected_type="JWS").claims
        assert '"preferred_username":"olanord"' in claims.replace(" ", "")

    def test_userinfo_returns_custom_claims(self):
        tokens = self.obtain_tokens()
        response = self.client.get(
            reverse("oauth2_provider:user-info"), headers={"authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["preferred_username"] == "olanord"
        assert data["email"] == "olanord@example.com"
        assert data["is_volunteer"] is False

    def test_current_user_endpoint_accepts_access_token(self):
        tokens = self.obtain_tokens()
        response = self.client.get(
            reverse("user-current-oauth2"), headers={"authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "olanord"
