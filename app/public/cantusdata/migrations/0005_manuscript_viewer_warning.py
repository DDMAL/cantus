# Generated migration for adding viewer_warning field to Manuscript model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cantusdata", "0004_alter_neumeexemplar_options_neumeexemplar_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="manuscript",
            name="viewer_warning",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Optional warning message to display if the manuscript viewer has compatibility issues",
            ),
        ),
    ]
