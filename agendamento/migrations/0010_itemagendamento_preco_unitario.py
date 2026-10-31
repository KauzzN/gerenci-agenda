from django.db import migrations, models


def preencher_precos_atuais(apps, schema_editor):
    ItemAgendamento = apps.get_model("agendamento", "ItemAgendamento")

    for item in ItemAgendamento.objects.select_related("servico").iterator():
        item.preco_unitario = item.servico.preco
        item.save(update_fields=["preco_unitario"])


def limpar_precos_preenchidos(apps, schema_editor):
    ItemAgendamento = apps.get_model("agendamento", "ItemAgendamento")
    ItemAgendamento.objects.update(preco_unitario=None)


class Migration(migrations.Migration):

    dependencies = [
        ("agendamento", "0009_remove_agendamento_atendido_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemagendamento",
            name="preco_unitario",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),
        migrations.RunPython(
            preencher_precos_atuais,
            limpar_precos_preenchidos,
        ),
        migrations.AlterField(
            model_name="itemagendamento",
            name="preco_unitario",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=8,
            ),
        ),
    ]
