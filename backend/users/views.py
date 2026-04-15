from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from bills.models import Bill
from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """Public endpoint to create a new user account."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send email verification link
        token = signing.dumps(user.pk, salt="email-verify")
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"
        send_mail(
            subject="Verify your BillClear AI email",
            message=f"Click the link to verify your email address:\n\n{verify_url}\n\nThis link expires in 7 days.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return Response(
            {"detail": "Account created successfully.", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Public endpoint that authenticates a user and returns JWT tokens.
    The refresh token is set as an httpOnly cookie; the access token is returned in the body.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                "access": access_token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

        # Set refresh token as httpOnly cookie
        cookie_secure = not settings.DEBUG
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=cookie_secure,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        )

        return response


class RefreshView(APIView):
    """Public endpoint to exchange a refresh token cookie for a new access token."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except (TokenError, InvalidToken):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({"access": access_token}, status=status.HTTP_200_OK)

        # Rotate the refresh cookie
        cookie_secure = not settings.DEBUG
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=cookie_secure,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )

        return response


class LogoutView(APIView):
    """Blacklists the refresh token and clears the cookie."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # Already invalid — that's fine

        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class ProfileView(APIView):
    """Get or update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class GoogleJWTView(View):
    """
    Bridge between allauth's session-based Google OAuth login and our SimpleJWT system.

    allauth redirects here (via LOGIN_REDIRECT_URL) after completing the Google OAuth
    dance and session-authenticating the user. We issue SimpleJWT tokens, clear the
    allauth session, set the refresh token as an httpOnly cookie, and redirect to the
    frontend OAuth callback page with the access token in the URL.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/login?error=oauth_failed"
            )

        user = request.user

        # Google-authenticated users have verified emails
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Clear allauth's session — we only want JWT auth going forward
        auth_logout(request)

        response = HttpResponseRedirect(
            f"{settings.FRONTEND_URL}/oauth/callback?access_token={access_token}"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )
        return response


class UserSavingsView(APIView):
    """Returns aggregate savings data for the authenticated user's dashboard."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from bills.models import LineItem
        from bills.services import calculate_bill_savings
        from disputes.models import Dispute

        user_bills = Bill.objects.filter(user=request.user)
        bill_ids = list(user_bills.values_list("id", flat=True))

        # Potential savings: apply per-item rules across all user line items
        all_line_items = LineItem.objects.filter(bill_id__in=bill_ids)
        potential_savings = calculate_bill_savings(all_line_items)

        # Confirmed savings: resolved disputes with a recorded savings_amount
        disputes = Dispute.objects.filter(bill_id__in=bill_ids, status="resolved")
        confirmed_savings = sum(
            d.savings_amount for d in disputes if d.savings_amount is not None
        )

        total_bills = user_bills.count()
        disputed_bills = user_bills.filter(status="disputed").count()
        resolved_bills = user_bills.filter(status="resolved").count()

        return Response(
            {
                "potential_savings": float(potential_savings),
                "confirmed_savings": float(confirmed_savings),
                "total_bills": total_bills,
                "disputed_bills": disputed_bills,
                "resolved_bills": resolved_bills,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """Verify a user's email address using a signed token from the verification link."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user_pk = signing.loads(token, salt="email-verify", max_age=86400 * 7)
            user = User.objects.get(pk=user_pk)
            if not user.email_verified:
                user.email_verified = True
                user.save(update_fields=["email_verified"])
            return Response({"detail": "Email verified successfully."})
        except signing.SignatureExpired:
            return Response({"detail": "This verification link has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except (signing.BadSignature, User.DoesNotExist):
            return Response({"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """Resend the email verification link to the authenticated user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response({"detail": "Email already verified."})
        token = signing.dumps(user.pk, salt="email-verify")
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"
        send_mail(
            subject="Verify your BillClear AI email",
            message=f"Click the link to verify your email address:\n\n{verify_url}\n\nThis link expires in 7 days.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return Response({"detail": "Verification email sent."})


class ChangePasswordView(APIView):
    """Change the authenticated user's password, re-issuing fresh JWT tokens."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Incorrect password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Re-issue tokens so the current session stays valid
        refresh = RefreshToken.for_user(user)
        response = Response({"access": str(refresh.access_token)}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )
        return response


class PasswordResetRequestView(APIView):
    """Request a password reset email. Never reveals whether the email exists."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            send_mail(
                subject="Reset your BillClear AI password",
                message=(
                    f"Click the link below to reset your password:\n\n{reset_url}\n\n"
                    "This link expires in 24 hours. If you didn't request this, you can ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass  # Don't reveal whether the email exists
        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    """Confirm a password reset using the uid/token from the reset link."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (ValueError, TypeError, User.DoesNotExist):
            return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "This link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password reset successfully. You can now sign in."})
