from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product

from .models import ProductReview


class ProductReviewApiTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Supplies", slug="supplies")
        self.product = Product.objects.create(
            category=category,
            name="Sample Product",
            slug="sample-product",
        )
        self.client = APIClient()
        self.review_url = "/api/v1/reviews/products/sample-product/"
        self.summary_url = f"{self.review_url}summary/"

    def create_review(self, **overrides):
        values = {
            "product": self.product,
            "display_name": "Reviewer",
            "rating": 4,
            "title": "Good product",
            "body": "This product worked well for my needs.",
        }
        values.update(overrides)
        return ProductReview.objects.create(**values)

    def test_guest_review_is_pending_and_not_public_until_approved(self):
        response = self.client.post(
            self.review_url,
            {
                "display_name": "Guest",
                "rating": 5,
                "title": "Excellent",
                "body": "Exactly as described.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        review = ProductReview.objects.get(product=self.product)
        self.assertEqual(review.status, ProductReview.Status.PENDING)
        self.assertIsNone(review.user)
        self.assertEqual(self.client.get(self.review_url).data["results"], [])
        self.assertEqual(
            self.client.get(self.summary_url).data,
            {"average_rating": "0.0", "review_count": 0},
        )

    def test_only_approved_reviews_contribute_to_public_rating(self):
        self.create_review(status=ProductReview.Status.APPROVED, rating=5)
        self.create_review(status=ProductReview.Status.PENDING, rating=1)
        self.create_review(status=ProductReview.Status.REJECTED, rating=1)

        summary = self.client.get(self.summary_url)
        reviews = self.client.get(self.review_url)

        self.assertEqual(
            summary.data,
            {"average_rating": "5.0", "review_count": 1},
        )
        self.assertEqual(len(reviews.data["results"]), 1)

    def test_customer_support_can_approve_review_and_it_becomes_public(self):
        call_command("sync_staff_roles")
        staff_user = get_user_model().objects.create_user(
            username="support",
            password="long-safe-password",
            is_staff=True,
        )
        staff_user.groups.add(Group.objects.get(name="Customer Support"))
        review = self.create_review()
        self.client.force_authenticate(user=staff_user)

        response = self.client.patch(
            f"/api/v1/reviews/manage/{review.pk}/",
            {"status": ProductReview.Status.APPROVED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.status, ProductReview.Status.APPROVED)
        self.assertEqual(review.moderated_by, staff_user)
        self.assertIsNotNone(review.moderated_at)

        self.client.force_authenticate(user=None)
        self.assertEqual(len(self.client.get(self.review_url).data["results"]), 1)

    def test_invalid_ratings_and_inactive_products_are_rejected(self):
        invalid_rating = self.client.post(
            self.review_url,
            {"rating": 6, "body": "Invalid rating"},
            format="json",
        )
        self.assertEqual(invalid_rating.status_code, 400)
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.post(
            self.review_url,
            {"rating": 5, "body": "Not accepted"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_product_with_review_history_cannot_be_deleted(self):
        call_command("sync_staff_roles")
        store_manager = get_user_model().objects.create_user(
            username="store-manager",
            password="long-safe-password",
            is_staff=True,
        )
        store_manager.groups.add(Group.objects.get(name="Store Manager"))
        self.create_review()
        self.client.force_authenticate(user=store_manager)

        response = self.client.delete(
            f"/api/v1/catalog/products/{self.product.slug}/"
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
