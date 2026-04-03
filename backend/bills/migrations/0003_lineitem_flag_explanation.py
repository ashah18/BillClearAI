from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineitem',
            name='flag_explanation',
            field=models.TextField(blank=True, default=''),
        ),
    ]
