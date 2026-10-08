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

    def test_persists_configured_working_days(self):
        response = self.update({
            "dias_funcionando": ["segunda", "terca", "domingo"]
        })

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.dias_funcionando,
            ["segunda", "terca", "domingo"],
        )
        self.assertEqual(
            response.json()["profile"]["dias_funcionando"],
            ["segunda", "terca", "domingo"],
        )

    def test_persists_empty_working_days(self):
        self.profile.dias_funcionando = ["segunda"]
        self.profile.save(update_fields=["dias_funcionando"])

        response = self.update({"dias_funcionando": []})

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.dias_funcionando, [])

    def test_rejects_invalid_working_days(self):
        response = self.update({"dias_funcionando": ["segunda", "invalido"]})

        self.assertEqual(response.status_code, 400)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.dias_funcionando, [])

    def test_rejects_non_list_working_days(self):
        response = self.update({"dias_funcionando": "segunda"})

        self.assertEqual(response.status_code, 400)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.dias_funcionando, [])

    def test_profile_endpoint_returns_public_business_fields(self):
        self.profile.endereco = "Rua das Flores, 10"
        self.profile.instagram = "@barbearia"
        self.profile.descricao = "Cortes e cuidados."
        self.profile.save(update_fields=["endereco", "instagram", "descricao"])

        response = self.client.get(
            "/api/usr/me/profile",
            **self.headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["endereco"], "Rua das Flores, 10")
        self.assertEqual(response.json()["instagram"], "@barbearia")
        self.assertEqual(response.json()["descricao"], "Cortes e cuidados.")
