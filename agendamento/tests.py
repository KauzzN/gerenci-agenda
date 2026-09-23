from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from cliente.models import Cliente, ClienteProfissional
from public.models import Profile
from servicos.models import Servico
from users.services.token_services import generate_access_token

from .booking_rules import has_schedule_conflict, within_business_hours
from .models import Agendamento


class SchedulingTestMixin:
    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="StrongPassword123!",
        )

    def create_profile(self, username, **kwargs):
        user = self.create_user(username)
        defaults = {
            "nome_negocio": "Barbearia Teste",
            "horario_inicio": time(8, 0),
            "horario_fim": time(18, 0),
            "inicio_almoco": time(12, 0),
            "fim_almoco": time(13, 0),
            "dias_funcionando": list(range(7)),
        }
        defaults.update(kwargs)
        return user, Profile.objects.create(user=user, **defaults)

    def create_client(self, username, phone):
        user = self.create_user(username)
        return Cliente.objects.create(
            user=user,
            nome=username.title(),
            telefone=phone,
        )

    def create_service(self, user, name="Corte", duration=30, active=True):
        return Servico.objects.create(
            user=user,
            nome=name,
            preco=Decimal("35.00"),
            duracao=duration,
            ativo=active,
        )

    def future_datetime(self, hour=10, minute=0):
        return timezone.make_aware(datetime(2030, 1, 7, hour, minute))


class ScheduleRuleTests(SchedulingTestMixin, TestCase):
    def setUp(self):
        self.professional, self.profile = self.create_profile("professional")
        self.client_record = self.create_client("client", "85999999999")
        self.service = self.create_service(self.professional)
        ClienteProfissional.objects.create(
            cliente=self.client_record,
            profile=self.profile,
        )

    def make_booking(self, start, end, status=Agendamento.Status.PENDENTE):
        return Agendamento.objects.create(
            profissional=self.professional,
            cliente=self.client_record,
            horario_inicio=start,
            horario_fim=end,
            status=status,
        )

    def test_overlapping_intervals_and_adjacent_intervals(self):
        existing_start = self.future_datetime(10)
        existing_end = self.future_datetime(11)
        self.make_booking(existing_start, existing_end)

        self.assertTrue(has_schedule_conflict(
            self.professional,
            self.future_datetime(9, 30),
            self.future_datetime(10, 30),
        ))
        self.assertTrue(has_schedule_conflict(
            self.professional,
            self.future_datetime(10, 30),
            self.future_datetime(11, 30),
        ))
        self.assertFalse(has_schedule_conflict(
            self.professional,
            self.future_datetime(9),
            existing_start,
        ))
        self.assertFalse(has_schedule_conflict(
            self.professional,
            existing_end,
            self.future_datetime(12),
        ))

    def test_cancelled_booking_does_not_block_active_booking(self):
        start = self.future_datetime(10)
        end = self.future_datetime(11)
        self.make_booking(start, end, Agendamento.Status.CANCELADO)
        self.assertFalse(has_schedule_conflict(
            self.professional,
            start,
            end,
        ))

    def test_business_hours_lunch_and_working_days(self):
        monday = self.future_datetime(10)
        self.assertTrue(within_business_hours(
            self.profile, monday, monday + timedelta(minutes=30)
        ))
        self.assertFalse(within_business_hours(
            self.profile,
            self.future_datetime(7, 30),
            self.future_datetime(8),
        ))
        self.assertFalse(within_business_hours(
            self.profile,
            self.future_datetime(17, 30),
            self.future_datetime(18, 30),
        ))
        self.assertFalse(within_business_hours(
            self.profile,
            self.future_datetime(11, 30),
            self.future_datetime(12, 30),
        ))
        self.assertTrue(within_business_hours(
            self.profile,
            self.future_datetime(11),
            self.future_datetime(12),
        ))
        self.assertTrue(within_business_hours(
            self.profile,
            self.future_datetime(13),
            self.future_datetime(14),
        ))

        self.profile.dias_funcionando = [1]
        self.profile.save(update_fields=["dias_funcionando"])
        self.assertFalse(within_business_hours(
            self.profile, monday, monday + timedelta(minutes=30)
        ))

    def test_status_transitions_match_business_rules(self):
        allowed = {
            Agendamento.Status.PENDENTE: {
                Agendamento.Status.ATENDIDO,
                Agendamento.Status.CANCELADO,
                Agendamento.Status.FALTOU,
            },
            Agendamento.Status.CANCELADO: {Agendamento.Status.CANCELADO},
            Agendamento.Status.ATENDIDO: {
                Agendamento.Status.ATENDIDO,
                Agendamento.Status.CANCELADO,
            },
            Agendamento.Status.FALTOU: {
                Agendamento.Status.FALTOU,
                Agendamento.Status.CANCELADO,
            },
        }

        for current, permitted in allowed.items():
            booking = self.make_booking(
                self.future_datetime(10),
                self.future_datetime(10, 30),
                current,
            )
            for next_status in Agendamento.Status:
                expected = next_status in permitted
                self.assertEqual(
                    booking.can_transition_to(next_status),
                    expected,
                    f"{current} -> {next_status}",
                )
            booking.delete()

    def test_active_and_inactive_relationships(self):
        relation = ClienteProfissional.objects.get(
            cliente=self.client_record,
            profile=self.profile,
        )
        self.assertTrue(relation.ativo)
        relation.ativo = False
        relation.save(update_fields=["ativo"])
        self.assertFalse(
            ClienteProfissional.objects.filter(
                cliente=self.client_record,
                profile=self.profile,
                ativo=True,
            ).exists()
        )


class CreateScheduleEndpointTests(SchedulingTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.professional, self.profile = self.create_profile("professional")
        self.client_record = self.create_client("client", "85999999999")
        ClienteProfissional.objects.create(
            cliente=self.client_record,
            profile=self.profile,
        )
        self.service = self.create_service(self.professional)

    def headers(self):
        return {
            "HTTP_AUTHORIZATION": (
                f"Bearer {generate_access_token(self.professional)}"
            )
        }

    def payload(self, **overrides):
        data = {
            "cliente_id": self.client_record.id,
            "servicos": [self.service.id],
            "horario_inicio": self.future_datetime().isoformat(),
        }
        data.update(overrides)
        return data

    def create(self, **overrides):
        return self.client.post(
            "/api/agendar/create",
            data=self.payload(**overrides),
            content_type="application/json",
            **self.headers(),
        )

    def test_read_rejects_invalid_calendar_dates_with_bad_request(self):
        for value in ("abc", "2026-99-99", "2026/10/15", "15-10-2026"):
            response = self.client.get(
                "/api/agendar/read",
                {"data": value},
                **self.headers(),
            )
            self.assertEqual(response.status_code, 400)

    def test_professional_creates_a_valid_schedule_with_normalized_response(self):
        response = self.create()

        self.assertEqual(response.status_code, 201)
        agendamento = response.json()["agendamento"]
        self.assertEqual(agendamento["cliente_id"], self.client_record.id)
        self.assertEqual(agendamento["servicos"][0]["id"], self.service.id)
        self.assertEqual(agendamento["status"], Agendamento.Status.PENDENTE)
        self.assertEqual(
            datetime.fromisoformat(agendamento["horario_fim"])
            - datetime.fromisoformat(agendamento["horario_inicio"]),
            timedelta(minutes=30),
        )
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_create_rejects_missing_client_or_services_without_persisting(self):
        for overrides in (
            {"cliente_id": None},
            {"servicos": []},
        ):
            response = self.create(**overrides)
            self.assertEqual(response.status_code, 400)

        self.assertEqual(Agendamento.objects.count(), 0)

    def test_create_rejects_unrelated_clients_services_and_invalid_times(self):
        other_professional, other_profile = self.create_profile("other-professional")
        other_client = self.create_client("other-client", "85888888888")
        ClienteProfissional.objects.create(
            cliente=other_client,
            profile=other_profile,
        )
        other_service = self.create_service(other_professional, "Barba")

        for overrides, expected_status in (
            ({"cliente_id": other_client.id}, 404),
            ({"servicos": [other_service.id]}, 400),
            ({"horario_inicio": "horario-invalido"}, 400),
        ):
            response = self.create(**overrides)
            self.assertEqual(response.status_code, expected_status)

        self.assertEqual(Agendamento.objects.count(), 0)

    def test_create_returns_conflict_without_creating_a_second_schedule(self):
        self.assertEqual(self.create().status_code, 201)

        response = self.create()

        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.json())
        self.assertEqual(Agendamento.objects.count(), 1)


class UpdateScheduleStatusEndpointTests(SchedulingTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.professional, self.profile = self.create_profile("professional")
        self.client_record = self.create_client("client", "85999999999")
        self.agendamento = Agendamento.objects.create(
            profissional=self.professional,
            cliente=self.client_record,
            horario_inicio=self.future_datetime(),
            horario_fim=self.future_datetime(10, 30),
        )

    def headers(self):
        return {
            "HTTP_AUTHORIZATION": (
                f"Bearer {generate_access_token(self.professional)}"
            )
        }

    def update_status(self, agendamento_id, status):
        return self.client.patch(
            f"/api/agendar/status/{agendamento_id}",
            data={"status": status},
            content_type="application/json",
            **self.headers(),
        )

    def test_pending_schedule_can_be_marked_as_attended(self):
        response = self.update_status(self.agendamento.id, "ATENDIDO")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Agendamento.Status.ATENDIDO)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.ATENDIDO)

    def test_pending_schedule_can_be_cancelled(self):
        response = self.update_status(self.agendamento.id, "CANCELADO")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Agendamento.Status.CANCELADO)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.CANCELADO)

    def test_invalid_status_transition_does_not_change_persisted_status(self):
        self.assertEqual(
            self.update_status(self.agendamento.id, "ATENDIDO").status_code,
            200,
        )

        response = self.update_status(self.agendamento.id, "FALTOU")

        self.assertEqual(response.status_code, 400)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.ATENDIDO)

    def test_missing_schedule_returns_not_found(self):
        response = self.update_status(999999, "ATENDIDO")

        self.assertEqual(response.status_code, 404)
