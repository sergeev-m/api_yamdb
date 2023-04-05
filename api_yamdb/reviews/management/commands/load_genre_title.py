import csv
import os

from django.core.management.base import BaseCommand

from reviews.models import GenreTitle


class Command(BaseCommand):
    help = 'load data from csv'

    def handle(self, *args, **options):
        csv_file = 'static/data/genre_title.csv'

        if not os.path.isfile(csv_file):
            print('file not found!')
            return

        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            cnt = {'all': 0, 'new': 0}
            for row in reader:
                try:
                    user, created = GenreTitle.objects.update_or_create(**row)
                    cnt['all'] += 1
                    if created:
                        cnt['new'] += 1
                except:
                    pass

        print('всего: {all}, добавлено в бд: {new}'.format(**cnt))
