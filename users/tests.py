from django.contrib.auth.models import User
from django.test import Client, TestCase

from public.models import Profile
from users.services.token_services import generate_access_token


class UpdateProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="professional", password="secret")
        self.profile = Profile.objects.create(user=self.user)
        self.other_user = User.objects.create_user(username="other", password="secret")
        Profile.objects.create(user=self.other_user, public_slug="slug-em-uso")

    def headers(self):
        return {
            "HTTP_AUTHORIZATION": f"Bearer {generate_access_token(self.user)}"
        }

    def update(self, payload):
        return self.client.patch(
            "/api/usr/update",
            data=payload,
            content_type="application/json",
            **self.headers(),
        )

    def test_updates_a_valid_slug_without_schedule_fields(self):
        response = self.update({"public_slug": "barbearia-teste"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"]["public_slug"], "barbearia-teste")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.public_slug, "barbearia-teste")

    def test_rejects_an_invalid_slug_without_persisting_it(self):
        response = self.update({"public_slug": "---"})

        self.assertEqual(response.status_code, 400)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.public_slug)

    def test_rejects_a_duplicate_slug_without_persisting_it(self):
        response = self.update({"public_slug": "slug-em-uso"})

        self.assertEqual(response.status_code, 409)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.public_slug)
