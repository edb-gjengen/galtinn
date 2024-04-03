from oauth2_provider.oauth2_validators import OAuth2Validator

from dusken.models import DuskenUser  # noqa: TCH001


class CustomOAuth2Validator(OAuth2Validator):
    oidc_claim_scope = None

    def get_additional_claims(self, request):
        """Ref: https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims"""
        # FIXME: Return everything regardless of scopes
        user: DuskenUser = request.user
        return {
            # profile scope claims
            "family_name": user.last_name,
            "given_name": user.first_name,
            "name": f"{user.first_name} {user.last_name}",
            "preferred_username": user.username,
            "updated_at": user.updated.isoformat(),
            # email scope claims
            "email": user.email,
            "email_verified": user.email_is_confirmed,
            # custom claims
            "is_volunteer": user.is_volunteer,
            "is_member": user.is_member,
        }

    def get_userinfo_claims(self, request):
        # FIXME: Return everything regardless of scopes
        return {
            **super().get_userinfo_claims(request),
            **self.get_additional_claims(request),
        }
