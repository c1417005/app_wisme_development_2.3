from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wisme', '0006_add_db_index_to_searched_word'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='image_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='サムネイルURL'),
        ),
    ]
