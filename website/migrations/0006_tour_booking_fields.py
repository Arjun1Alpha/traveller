from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0005_category_summary_tour_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="tour",
            name="currency",
            field=models.CharField(
                default="EUR",
                help_text="ISO 4217 code shown with price (e.g. EUR, GBP, USD).",
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="duration_hours",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("2.50"),
                help_text="Typical guided time in hours.",
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.25"))
                ],
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="free_cancellation",
            field=models.BooleanField(
                default=True,
                help_text="Show free-cancellation badge when true.",
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="group_size_max",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Maximum guests per departure (empty if it varies).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="languages",
            field=models.CharField(
                blank=True,
                help_text="Languages offered, comma-separated (searchable on tour lists).",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="price_from",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Lowest typical adult price per person (empty = ask us).",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="rating_average",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("4.70"),
                help_text="Display rating 0–5 (e.g. from partner surveys).",
                max_digits=3,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0")),
                    django.core.validators.MaxValueValidator(Decimal("5")),
                ],
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="review_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Number of reviews this rating is based on.",
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="skip_the_line",
            field=models.BooleanField(
                default=False,
                help_text="Priority / timed entry or skip-the-line style access.",
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="wheelchair_accessible",
            field=models.BooleanField(
                default=False,
                help_text="Marketed as wheelchair-friendly (partial or full).",
            ),
        ),
    ]
