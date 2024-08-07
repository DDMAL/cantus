# Generated by Django 4.2.3 on 2023-09-13 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Concordance",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("letter_code", models.CharField(max_length=1, unique=True)),
                (
                    "institution_city",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "institution_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "library_manuscript_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("date", models.CharField(blank=True, max_length=255, null=True)),
                ("location", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "rism_code",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="RISM code"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Folio",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.CharField(blank=True, max_length=50, null=True)),
                ("image_uri", models.CharField(blank=True, max_length=255, null=True)),
                ("image_link", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "ordering": ["number"],
            },
        ),
        migrations.CreateModel(
            name="Plugin",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="NeumeExemplar",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("x_coord", models.IntegerField()),
                ("y_coord", models.IntegerField()),
                ("width", models.IntegerField()),
                ("height", models.IntegerField()),
                (
                    "folio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cantusdata.folio",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Manuscript",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("siglum", models.CharField(blank=True, max_length=255, null=True)),
                ("date", models.CharField(blank=True, max_length=50, null=True)),
                ("provenance", models.CharField(blank=True, max_length=100, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("public", models.BooleanField(default=False)),
                (
                    "is_mapped",
                    models.CharField(
                        choices=[
                            ("UNMAPPED", "Unmapped"),
                            ("PENDING", "Pending"),
                            ("MAPPED", "Mapped"),
                        ],
                        default="UNMAPPED",
                        max_length=10,
                    ),
                ),
                (
                    "dbl_folio_img",
                    models.BooleanField(
                        default=False, verbose_name="Double-folio images"
                    ),
                ),
                ("chants_loaded", models.BooleanField(default=False)),
                ("cantus_url", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "csv_export_url",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "manifest_url",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "plugins",
                    models.ManyToManyField(
                        blank=True, related_name="plugins", to="cantusdata.plugin"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="folio",
            name="manuscript",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cantusdata.manuscript"
            ),
        ),
        migrations.CreateModel(
            name="Chant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("marginalia", models.CharField(blank=True, max_length=255, null=True)),
                ("sequence", models.PositiveSmallIntegerField()),
                ("cantus_id", models.CharField(blank=True, max_length=50, null=True)),
                ("feast", models.CharField(blank=True, max_length=255, null=True)),
                ("office", models.CharField(blank=True, max_length=255, null=True)),
                ("genre", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "lit_position",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("mode", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "differentia",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("finalis", models.CharField(blank=True, max_length=255, null=True)),
                ("incipit", models.TextField(blank=True, null=True)),
                ("full_text", models.TextField(blank=True, null=True)),
                ("full_text_ms", models.TextField(blank=True, null=True)),
                ("volpiano", models.TextField(blank=True, null=True)),
                (
                    "cdb_uri",
                    models.PositiveIntegerField(
                        null=True, verbose_name="Cantus DB URI"
                    ),
                ),
                (
                    "concordances",
                    models.ManyToManyField(
                        blank=True,
                        related_name="concordances",
                        to="cantusdata.concordance",
                    ),
                ),
                (
                    "folio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cantusdata.folio",
                    ),
                ),
                (
                    "manuscript",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cantusdata.manuscript",
                    ),
                ),
            ],
            options={
                "ordering": ["sequence"],
            },
        ),
        migrations.AddConstraint(
            model_name="manuscript",
            constraint=models.CheckConstraint(
                check=models.Q(("is_mapped__in", ["UNMAPPED", "PENDING", "MAPPED"])),
                name="is_mapped_status",
            ),
        ),
    ]
