"""
Adds the PUBLISHING status.

The check constraint bakes the allowed values into its SQL, so a new choice
means dropping and re-adding it -- which is what the generated operations below
do. Purely additive otherwise: no existing row changes, since nothing is ever
written as PUBLISHING except by a claim made after this migration runs.
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cantusdata", "0007_meisubmission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="meisubmission",
            name="mei_submission_status",
        ),
        migrations.AlterField(
            model_name="meisubmission",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending review"),
                    ("PUBLISHING", "Publishing"),
                    ("PUBLISHED", "Published"),
                    ("CORRECTION_REQUESTED", "Correction requested"),
                    ("REFUSED", "Refused"),
                    ("SUPERSEDED", "Superseded by a newer submission"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="meisubmission",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "status__in",
                        [
                            "PENDING",
                            "PUBLISHING",
                            "PUBLISHED",
                            "CORRECTION_REQUESTED",
                            "REFUSED",
                            "SUPERSEDED",
                        ],
                    )
                ),
                name="mei_submission_status",
            ),
        ),
    ]
