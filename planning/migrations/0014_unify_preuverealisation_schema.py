# Convertit l'ancien schéma de PreuveRealisation (type_preuve, titre, lien, created_at, updated_at)
# vers le schéma unifié (type, description, url, uploaded_at, annee) si nécessaire.

from django.db import migrations


def unify_schema(apps, schema_editor):
    connection = schema_editor.connection
    table = 'planning_preuverealisation'
    with connection.cursor() as cursor:
        columns = [c.name for c in connection.introspection.get_table_description(cursor, table)]
    if 'type_preuve' not in columns:
        return

    qn = schema_editor.quote_name
    statements = [
        f"ALTER TABLE {qn(table)} CHANGE {qn('type_preuve')} {qn('type')} varchar(20) NOT NULL",
        f"ALTER TABLE {qn(table)} CHANGE {qn('lien')} {qn('url')} varchar(200) NULL",
        f"ALTER TABLE {qn(table)} CHANGE {qn('titre')} {qn('description')} longtext NULL",
        f"ALTER TABLE {qn(table)} CHANGE {qn('created_at')} {qn('uploaded_at')} datetime(6) NOT NULL",
        f"ALTER TABLE {qn(table)} DROP COLUMN {qn('updated_at')}",
        f"ALTER TABLE {qn(table)} ADD COLUMN {qn('annee')} integer UNSIGNED NOT NULL DEFAULT 0",
        f"ALTER TABLE {qn(table)} ALTER COLUMN {qn('annee')} DROP DEFAULT",
    ]
    for sql in statements:
        schema_editor.execute(sql)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('planning', '0013_quarterlyreport'),
    ]

    operations = [
        migrations.RunPython(unify_schema, migrations.RunPython.noop),
    ]
