from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import CustomerFeedback


class CustomerFeedbackApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.feedback_url = "/api/v1/feedback/"
        call_command("sync_staff_roles")
        self.support_user = get_user_model().objects.create_user(
            username="support",
            password="long-safe-password",
            is_staff=True,
        )
        self.support_user.groups.add(Group.objects.get(name="Customer Support"))

    def test_guest_can_submit_feedback_but_cannot_read_private_inbox(self):
        response = self.client.post(
            self.feedback_url,
            {
                "name": "Guest Customer",
                "email": "guest@example.test",
                "category": "website",
                "message": "The catalog was easy to use.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        feedback = CustomerFeedback.objects.get()
        self.assertIsNone(feedback.user)
        self.assertEqual(feedback.status, CustomerFeedback.Status.NEW)
        self.assertEqual(self.client.get(self.feedback_url).status_code, 405)
        self.assertEqual(
            self.client.get("/api/v1/feedback/manage/").status_code,
            403,
        )

    def test_customer_support_can_manage_feedback(self):
        self.client.post(
            self.feedback_url,
            {"message": "Please contact me about my order."},
            format="json",
        )
        self.client.force_authenticate(user=self.support_user)

        session_user = self.client.get("/api/v1/auth/me/")
        self.assertIn(
            "feedback.view_customerfeedback",
            session_user.data["permissions"],
        )
        self.assertIn(
            "reviews.view_productreview",
            session_user.data["permissions"],
        )

        inbox = self.client.get("/api/v1/feedback/manage/")

        self.assertEqual(inbox.status_code, 200)
        feedback_id = inbox.data["results"][0]["id"]
        response = self.client.patch(
            f"/api/v1/feedback/manage/{feedback_id}/",
            {
                "status": CustomerFeedback.Status.IN_PROGRESS,
                "staff_notes": "Follow up with the customer.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        feedback = CustomerFeedback.objects.get(pk=feedback_id)
        self.assertEqual(feedback.status, CustomerFeedback.Status.IN_PROGRESS)
        self.assertEqual(feedback.staff_notes, "Follow up with the customer.")

    def test_blank_feedback_is_rejected(self):
        response = self.client.post(
            self.feedback_url,
            {"message": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
