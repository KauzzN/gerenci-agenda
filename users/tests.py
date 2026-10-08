import logging
import re
from datetime import time

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.logging import log_event
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

    def test_updates_only_lunch_using_existing_expedient(self):
        self.profile.horario_inicio = time(8)
        self.profile.horario_fim = time(18)
        self.profile.inicio_almoco = time(12)
        self.profile.fim_almoco = time(13)
        self.profile.save()

        response = self.update({
            "inicio_almoco": "12:30",
            "fim_almoco": "13:30",
        })

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.horario_inicio, time(8))
        self.assertEqual(self.profile.horario_fim, time(18))
        self.assertEqual(self.profile.inicio_almoco, time(12, 30))
        self.assertEqual(self.profile.fim_almoco, time(13, 30))

    def test_rejects_partial_schedule_without_existing_expedient(self):
        response = self.update({
            "inicio_almoco": "12:30",
            "fim_almoco": "13:30",
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_rejects_invalid_schedule_types_without_server_error(self):
        response = self.update({
            "horario_inicio": [],
            "horario_fim": "18:00",
        })

        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_profile_field_types_without_server_error(self):
        response = self.update({
            "nome_negocio": ["Barbearia"],
        })

        self.assertEqual(response.status_code, 400)

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

    def test_clears_optional_profile_fields(self):
        self.profile.endereco = "Rua das Flores, 10"
        self.profile.instagram = "@barbearia"
        self.profile.descricao = "Cortes e cuidados."
        self.profile.save(update_fields=["endereco", "instagram", "descricao"])

        response = self.update({
            "endereco": "",
            "instagram": "",
            "descricao": "",
        })

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.endereco, "")
        self.assertEqual(self.profile.instagram, "")
        self.assertEqual(self.profile.descricao, "")


class LoggingFoundationTests(TestCase):
    def test_request_id_is_returned_and_reuses_a_valid_value(self):
        response = self.client.get(
            "/api/usr/me",
            HTTP_X_REQUEST_ID="request-test-123",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers["X-Request-ID"],
            "request-test-123",
        )

    def test_request_id_is_generated_for_invalid_values(self):
        response = self.client.get(
            "/api/usr/me",
            HTTP_X_REQUEST_ID="invalid request id",
        )

        self.assertEqual(response.status_code, 401)
        self.assertRegex(
            response.headers["X-Request-ID"],
            re.compile(r"^[0-9a-f-]{36}$"),
        )

    def test_login_failure_is_logged_without_credentials(self):
        with self.assertLogs("users.views", level=logging.WARNING) as captured:
            response = self.client.post(
                "/api/usr/login",
                data={
                    "username": "missing-user",
                    "password": "not-logged",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 404)
        output = "\n".join(captured.output)
        self.assertIn("event=auth.login_failed", output)
        self.assertIn("reason=invalid_credentials", output)
        self.assertNotIn("not-logged", output)

    def test_log_event_filters_sensitive_fields(self):
        with self.assertLogs("users.tests", level=logging.INFO) as captured:
            log_event(
                logging.getLogger("users.tests"),
                logging.INFO,
                "test.event",
                user_id=42,
                password="secret",
                access_token="token",
                safe_value="present",
            )

        output = "\n".join(captured.output)
        self.assertIn("event=test.event", output)
        self.assertIn("safe_value=present", output)
        self.assertNotIn("secret", output)
        self.assertNotIn("token", output)
