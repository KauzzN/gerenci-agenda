from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from public.models import Profile
from users.services.token_services import generate_access_token

from .models import Servico


class ServiceEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.professional = User.objects.create_user(
            username="professional",
            password="StrongPassword123!",
        )
        Profile.objects.create(
            user=self.professional,
            nome_negocio="Barbearia Teste",
        )
        self.other_professional = User.objects.create_user(
            username="other",
            password="StrongPassword123!",
        )
        Profile.objects.create(user=self.other_professional)

    def headers(self, user):
        return {
            "HTTP_AUTHORIZATION": (
                f"Bearer {generate_access_token(user)}"
            )
        }

    def test_professional_can_create_valid_service(self):
        response = self.client.post(
            "/api/serv/create",
            data={
                "nome": "Corte",
                "preco": "35.00",
                "duracao": 30,
                "descricao": "",
                "cor": "#000000",
            },
            content_type="application/json",
            **self.headers(self.professional),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Servico.objects.filter(
                user=self.professional,
                nome="Corte",
            ).exists()
        )
        service = Servico.objects.get(
            user=self.professional,
            nome="Corte",
        )
        self.assertEqual(response.json()["servico"]["id"], service.id)

    def test_invalid_price_and_duration_are_rejected(self):
        payloads = (
            {
                "nome": "Preço inválido",
                "preco": "-1.00",
                "duracao": 30,
                "descricao": "",
                "cor": "#000000",
            },
            {
                "nome": "Duração inválida",
                "preco": "10.00",
                "duracao": 0,
                "descricao": "",
                "cor": "#000000",
            },
        )
        for payload in payloads:
            response = self.client.post(
                "/api/serv/create",
                data=payload,
                content_type="application/json",
                **self.headers(self.professional),
            )
            self.assertEqual(response.status_code, 400)

    def test_professional_cannot_access_another_professional_service(self):
        service = Servico.objects.create(
            user=self.other_professional,
            nome="Serviço privado",
            preco=Decimal("20.00"),
            duracao=30,
        )
        response = self.client.get(
            f"/api/serv/read/{service.id}",
            **self.headers(self.professional),
        )
        self.assertEqual(response.status_code, 404)
