# Generated migration to add Axe model and migrate Effet from PlanAction to Axe

import django.db.models.deletion
from django.db import migrations, models


def migrate_effets_to_axes(apps, schema_editor):
    """Create a default Axe for each PlanAction that has Effets, and assign Effets to it."""
    PlanAction = apps.get_model('planning', 'PlanAction')
    Axe = apps.get_model('planning', 'Axe')
    Effet = apps.get_model('planning', 'Effet')

    for plan in PlanAction.objects.all():
        effets = Effet.objects.filter(plan=plan)
        if effets.exists():
            # Create a default Axe for this plan
            axe = Axe.objects.create(
                plan=plan,
                titre=f"Axe 1 - {plan.titre[:50]}",
                couts=plan.couts if plan.couts else [0.0] * plan.horizon,
                nombre_effets=effets.count(),
                nombre_produits=plan.nombre_produits,
                nombre_actions=plan.nombre_actions,
                nombre_activites=plan.nombre_activites,
                reference="1",
            )
            # Assign all effets to this axe
            effets.update(axe=axe)


def reverse_migrate(apps, schema_editor):
    """Move Effets back to PlanAction (reverse migration)."""
    Effet = apps.get_model('planning', 'Effet')
    for effet in Effet.objects.select_related('axe__plan').all():
        if effet.axe:
            effet.plan = effet.axe.plan
            effet.save()


class Migration(migrations.Migration):

    dependencies = [
        ('planning', '0010_alter_action_options_alter_activitelog_options_and_more'),
    ]

    operations = [
        # Step 1: Create the Axe model
        migrations.CreateModel(
            name='Axe',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('titre', models.CharField(max_length=500)),
                ('couts', models.JSONField(default=list)),
                ('nombre_effets', models.PositiveIntegerField(default=0)),
                ('nombre_produits', models.PositiveIntegerField(default=0)),
                ('nombre_actions', models.PositiveIntegerField(default=0)),
                ('nombre_activites', models.PositiveIntegerField(default=0)),
                ('reference', models.CharField(blank=True, max_length=50)),
                ('plan', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='plan_axe',
                    to='planning.planaction',
                )),
            ],
            options={
                'verbose_name': 'Axe',
                'verbose_name_plural': 'Axes',
            },
        ),
        # Step 2: Add nullable axe FK to Effet
        migrations.AddField(
            model_name='effet',
            name='axe',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='axe_effet',
                to='planning.axe',
            ),
            preserve_default=False,
        ),
        # Step 3: Migrate existing data
        migrations.RunPython(migrate_effets_to_axes, reverse_migrate),
        # Step 4: Make axe non-nullable
        migrations.AlterField(
            model_name='effet',
            name='axe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='axe_effet',
                to='planning.axe',
            ),
        ),
        # Step 5: Remove old plan FK from Effet
        migrations.RemoveField(
            model_name='effet',
            name='plan',
        ),
    ]
