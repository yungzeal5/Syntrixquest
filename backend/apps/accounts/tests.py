from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import CustomerAddress


class CustomerRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"
        self.password = "Safe-Long-Password-984!"

    def test_registration_creates_user_and_profile_without_returning_password(self):
        response = self.client.post(
            self.url,
            {
                "username": "new-customer",
                "email": "customer@example.com",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["username"], "new-customer")
        self.assertEqual(response.data["email"], "customer@example.com")
        self.assertNotIn("password", response.data)

        user = get_user_model().objects.get(username="new-customer")
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.customerprofile.email, "customer@example.com")

    def test_registration_allows_omitting_email(self):
        response = self.client.post(
            self.url,
            {"username": "no-email", "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "")
        self.assertIsNone(
            get_user_model().objects.get(username="no-email").customerprofile.email
        )

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        self.client.post(
            self.url,
            {
                "username": "first-customer",
                "email": "customer@example.com",
                "password": self.password,
            },
            format="json",
        )
        response = self.client.post(
            self.url,
            {
                "username": "second-customer",
                "email": "CUSTOMER@example.com",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_registration_rejects_weak_password(self):
        response = self.client.post(
            self.url,
            {"username": "weak-password", "password": "password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)


class SessionAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            username="session-customer",
            password="Safe-Long-Password-984!",
            email="session@example.com",
        )
        self.csrf_url = "/api/v1/auth/csrf/"
        self.login_url = "/api/v1/auth/login/"
        self.logout_url = "/api/v1/auth/logout/"
        self.user_url = "/api/v1/auth/me/"

    def get_csrf_token(self):
        response = self.client.get(self.csrf_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", self.client.cookies)
        return response.data["csrfToken"]

    def test_login_requires_csrf_and_creates_authenticated_session(self):
        payload = {
            "username": "session-customer",
            "password": "Safe-Long-Password-984!",
        }

        rejected = self.client.post(
            self.login_url,
            payload,
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
        )
        self.assertEqual(rejected.status_code, 403)

        csrf_token = self.get_csrf_token()
        response = self.client.post(
            self.login_url,
            payload,
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertFalse(response.data["is_staff"])
        self.assertFalse(response.data["is_superuser"])
        self.assertEqual(response.data["permissions"], [])
        self.assertIn("sessionid", self.client.cookies)

        current_user = self.client.get(self.user_url)
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.data["id"], self.user.id)

    def test_login_rejects_invalid_credentials(self):
        csrf_token = self.get_csrf_token()
        response = self.client.post(
            self.login_url,
            {"username": self.user.username, "password": "incorrect-password"},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid username or password.")

    def test_logout_requires_a_session_and_ends_it(self):
        self.client.force_login(self.user)
        csrf_token = self.get_csrf_token()
        response = self.client.post(
            self.logout_url,
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 204)
        current_user = self.client.get(self.user_url)
        self.assertNotEqual(current_user.status_code, 200)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            username="reset-customer",
            password="Original-Password-984!",
            email="reset@example.com",
        )
        self.csrf_url = "/api/v1/auth/csrf/"
        self.request_url = "/api/v1/auth/password-reset/"
        self.confirm_url = "/api/v1/auth/password-reset/confirm/"

    def post_with_csrf(self, url, data):
        csrf_response = self.client.get(self.csrf_url)
        self.assertEqual(csrf_response.status_code, 200)
        return self.client.post(
            url,
            data,
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"],
        )

    def get_reset_link_data(self):
        response = self.post_with_csrf(
            self.request_url,
            {"email": self.user.email},
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)

        link = next(
            line.strip()
            for line in mail.outbox[0].body.splitlines()
            if "http://localhost:3000/reset-password?" in line
        )
        return parse_qs(urlparse(link).query)

    def test_unknown_email_gets_generic_response_without_sending_email(self):
        response = self.post_with_csrf(
            self.request_url,
            {"email": "unknown@example.com"},
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data["detail"],
            "If an account with that email exists, reset instructions will be sent.",
        )
        self.assertEqual(mail.outbox, [])

    def test_existing_email_receives_reset_link(self):
        link_data = self.get_reset_link_data()

        self.assertIn("uid", link_data)
        self.assertIn("token", link_data)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_confirm_changes_password_and_invalidates_the_reset_token(self):
        link_data = self.get_reset_link_data()
        payload = {
            "uid": link_data["uid"][0],
            "token": link_data["token"][0],
            "new_password": "Brand-New-Password-839!",
            "new_password_confirm": "Brand-New-Password-839!",
        }

        response = self.post_with_csrf(self.confirm_url, payload)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["new_password"]))

        reused_response = self.post_with_csrf(self.confirm_url, payload)
        self.assertEqual(reused_response.status_code, 400)
        self.assertEqual(
            reused_response.data["detail"],
            "This password-reset link is invalid or has expired.",
        )

    def test_confirm_rejects_expired_reset_token(self):
        link_data = self.get_reset_link_data()
        payload = {
            "uid": link_data["uid"][0],
            "token": link_data["token"][0],
            "new_password": "Brand-New-Password-839!",
            "new_password_confirm": "Brand-New-Password-839!",
        }

        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            response = self.post_with_csrf(self.confirm_url, payload)

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Original-Password-984!"))

    def test_confirm_rejects_malformed_reset_link(self):
        response = self.post_with_csrf(
            self.confirm_url,
            {
                "uid": "!",
                "token": "invalid",
                "new_password": "Brand-New-Password-839!",
                "new_password_confirm": "Brand-New-Password-839!",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "This password-reset link is invalid or has expired.",
        )

    def test_confirm_applies_password_match_and_strength_validation(self):
        link_data = self.get_reset_link_data()
        payload = {
            "uid": link_data["uid"][0],
            "token": link_data["token"][0],
            "new_password": "Brand-New-Password-839!",
            "new_password_confirm": "Different-Password-839!",
        }

        mismatch_response = self.post_with_csrf(self.confirm_url, payload)

        self.assertEqual(mismatch_response.status_code, 400)
        self.assertIn("new_password_confirm", mismatch_response.data)

        payload["new_password"] = "password"
        payload["new_password_confirm"] = "password"
        weak_password_response = self.post_with_csrf(self.confirm_url, payload)

        self.assertEqual(weak_password_response.status_code, 400)
        self.assertIn("new_password", weak_password_response.data)

    def test_reset_request_is_rate_limited(self):
        for attempt in range(5):
            response = self.post_with_csrf(
                self.request_url,
                {"email": f"unknown-{attempt}@example.com"},
            )
            self.assertEqual(response.status_code, 202)

        throttled_response = self.post_with_csrf(
            self.request_url,
            {"email": "another-unknown@example.com"},
        )

        self.assertEqual(throttled_response.status_code, 429)

    def test_reset_request_requires_csrf(self):
        response = self.client.post(
            self.request_url,
            {"email": self.user.email},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(mail.outbox, [])


class CustomerAddressTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="address-owner")
        self.other_user = user_model.objects.create_user(username="other-customer")
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.address_url = "/api/v1/auth/addresses/"

    def address_data(self, **overrides):
        data = {
            "label": "Home",
            "recipient_name": "Customer Name",
            "phone_number": "+233200000000",
            "address_line_1": "12 Example Road",
            "city": "Accra",
            "region": "Greater Accra",
            "country_code": "gh",
        }
        data.update(overrides)
        return data

    def test_customer_can_create_and_list_only_their_addresses(self):
        own_address = CustomerAddress.objects.create(
            user=self.owner,
            recipient_name="Owner",
            phone_number="+233200000000",
            address_line_1="12 Example Road",
            city="Accra",
            region="Greater Accra",
            country_code="GH",
        )
        CustomerAddress.objects.create(
            user=self.other_user,
            recipient_name="Other",
            phone_number="+233211111111",
            address_line_1="34 Other Road",
            city="Kumasi",
            region="Ashanti",
            country_code="GH",
        )

        response = self.client.get(self.address_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [own_address.id])

    def test_address_creation_uses_authenticated_customer(self):
        response = self.client.post(
            self.address_url,
            self.address_data(user=self.other_user.id),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        address = CustomerAddress.objects.get(pk=response.data["id"])
        self.assertEqual(address.user, self.owner)
        self.assertEqual(response.data["country_code"], "GH")

    def test_customer_cannot_read_update_or_delete_another_customers_address(self):
        address = CustomerAddress.objects.create(
            user=self.other_user,
            recipient_name="Other",
            phone_number="+233211111111",
            address_line_1="34 Other Road",
            city="Kumasi",
            region="Ashanti",
            country_code="GH",
        )
        detail_url = f"{self.address_url}{address.id}/"

        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.patch(
                detail_url,
                {"city": "Tamale"},
                format="json",
            ).status_code,
            404,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, 404)

    def test_anonymous_customer_cannot_list_addresses(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.address_url)

        self.assertEqual(response.status_code, 403)
