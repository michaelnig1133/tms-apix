from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import BlacklistedToken, OutstandingToken

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None  

        user, token = result
        if user.is_deleted:
            raise AuthenticationFailed("Your account is deactivated. Contact admin.")
        if OutstandingToken.objects.filter(token=token).exists():
            if BlacklistedToken.objects.filter(token=token).exists():
                raise AuthenticationFailed("Token has been blacklisted. Please log in again.")

        return user, token

