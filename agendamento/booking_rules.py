from datetime import datetime

from agendamento.models import Agendamento
from servicos.models import Servico


def parse_service_ids(values):
    if (
        len(values) == 1
        and isinstance(values[0], str)
        and "," in values[0]
    ):
        values = values[0].split(",")

    try:
        service_ids = [int(value) for value in values]
    except (TypeError, ValueError):
        return None

    if (
        not service_ids
        or any(service_id <= 0 for service_id in service_ids)
        or len(service_ids) != len(set(service_ids))
    ):
        return None

    return service_ids


def load_active_services(user, service_ids):
    services = list(
        Servico.objects.filter(
            id__in=service_ids,
            user=user,
            ativo=True,
        )
    )
    services_by_id = {service.id: service for service in services}
    if len(services) != len(service_ids):
        return None

    return [services_by_id[service_id] for service_id in service_ids]


def overlaps_lunch(profile, inicio, fim):
    return bool(
        profile.inicio_almoco
        and profile.fim_almoco
        and inicio.time() < profile.fim_almoco
        and fim.time() > profile.inicio_almoco
    )


def is_working_day(profile, appointment_date):
    configured_days = profile.dias_funcionando
    if not configured_days:
        return True

    weekday = appointment_date.weekday()
    names = (
        ("segunda", "segunda-feira", "monday"),
        ("terca", "terça", "terça-feira", "tuesday"),
        ("quarta", "quarta-feira", "wednesday"),
        ("quinta", "quinta-feira", "quinta-feira", "thursday"),
        ("sexta", "sexta-feira", "friday"),
        ("sabado", "sábado", "sábado", "saturday"),
        ("domingo", "sunday"),
    )

    for value in configured_days:
        if isinstance(value, int) and value == weekday:
            return True
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in names[weekday]:
                return True

    return False


def within_business_hours(profile, inicio, fim):
    if profile.horario_inicio is None or profile.horario_fim is None:
        return False

    return (
        inicio.date() == fim.date()
        and is_working_day(profile, inicio.date())
        and inicio.time() >= profile.horario_inicio
        and fim.time() <= profile.horario_fim
        and not overlaps_lunch(profile, inicio, fim)
    )


def has_schedule_conflict(professional, inicio, fim, exclude_id=None):
    conflicts = Agendamento.objects.filter(
        profissional=professional,
        horario_inicio__lt=fim,
        horario_fim__gt=inicio,
    ).exclude(status=Agendamento.Status.CANCELADO)

    if exclude_id is not None:
        conflicts = conflicts.exclude(id=exclude_id)

    return conflicts.exists()
