from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from cliente.models import Cliente, ClienteProfissional
from public.models import Profile
from servicos.models import Servico
from users.services.token_services import generate_access_token


class PublicBookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.professional = User.objects.create_user(
            username="professional",
            password="StrongPassword123!",
        )
        self.profile = Profile.objects.create(
            user=self.professional,
            nome_negocio="Barbearia Teste",
            public_slug="barbearia-teste",
            horario_inicio=time(8),
            horario_fim=time(18),
            inicio_almoco=time(12),
            fim_almoco=time(13),
            dias_funcionando=list(range(7)),
        )
        self.client_user = User.objects.create_user(
            username="client",
            password="StrongPassword123!",
        )
        self.client_record = Cliente.objects.create(
            user=self.client_user,
            nome="Client",
            telefone="85999999999",
        )
        ClienteProfissional.objects.create(
            cliente=self.client_record,
            profile=self.profile,
        )
        self.service = self.create_service("Corte", 30)

    def create_service(self, name, duration, active=True, user=None):
        return Servico.objects.create(
            user=user or self.professional,
            nome=name,
            preco=Decimal("35.00"),
            duracao=duration,
            ativo=active,
        )

    def headers(self, user=None):
        user = user or self.client_user
        return {
            "HTTP_AUTHORIZATION": (
                f"Bearer {generate_access_token(user)}"
            )
        }

    def start(self, hour=10):
        return timezone.make_aware(datetime(2030, 1, 7, hour))

    def post_booking(self, services):
        return self.client.post(
            "/api/public/barbearia-teste/agendar",
            data={
                "servicos": services,
                "horario_inicio": self.start().isoformat(),
            },
            content_type="application/json",
            **self.headers(),
        )

    def test_public_profile_is_available_without_client_token(self):
        response = self.client.get("/api/public/barbearia-teste/barbearia")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["barbearia"], "barbearia-teste")
        self.assertEqual(response.json()["servicos"][0]["id"], self.service.id)

    def test_unknown_public_slug_returns_not_found(self):
        response = self.client.get("/api/public/inexistente/barbearia")

        self.assertEqual(response.status_code, 404)

    def test_active_client_can_book_and_total_duration_is_persisted(self):
        second_service = self.create_service("Barba", 30)
        response = self.post_booking([self.service.id, second_service.id])
        self.assertEqual(response.status_code, 201)
        booking = self.client_record.agendamentos.get()
        self.assertEqual(
            booking.horario_fim - booking.horario_inicio,
            timedelta(minutes=60),
        )

    def test_unavailable_service_inputs_are_rejected(self):
        inactive = self.create_service("Inativo", 30, active=False)
        other_user = User.objects.create_user(username="other")
        Profile.objects.create(
            user=other_user,
            public_slug="outra-barbearia",
        )
        foreign = self.create_service("Estrangeiro", 30, user=other_user)

        for services in (
            [],
            [self.service.id, self.service.id],
            [inactive.id],
            [foreign.id],
            [999999],
        ):
            response = self.post_booking(services)
            self.assertEqual(response.status_code, 400)

        self.assertFalse(self.client_record.agendamentos.exists())

    def test_missing_and_inactive_relationships_are_rejected(self):
        relation = ClienteProfissional.objects.get(
            cliente=self.client_record,
            profile=self.profile,
        )
        relation.delete()
        response = self.post_booking([self.service.id])
        self.assertEqual(response.status_code, 403)

        ClienteProfissional.objects.create(
            cliente=self.client_record,
            profile=self.profile,
            ativo=False,
        )
        response = self.post_booking([self.service.id])
        self.assertEqual(response.status_code, 403)

    def test_active_booking_blocks_and_cancelled_booking_does_not(self):
        response = self.post_booking([self.service.id])
        self.assertEqual(response.status_code, 201)

        response = self.post_booking([self.service.id])
        self.assertEqual(response.status_code, 409)

        self.client_record.agendamentos.update(status="CANCELADO")
        response = self.post_booking([self.service.id])
        self.assertEqual(response.status_code, 201)
