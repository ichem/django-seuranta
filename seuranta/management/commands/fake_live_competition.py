from datetime import timedelta
import math
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from seuranta.models import Competition, Competitor, Route
from seuranta.utils import make_random_code
from seuranta.utils.geo import GeoLocation, GeoLocationSeries


class Command(BaseCommand):
    publisher = None
    competition = None

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--nb_competitors',
            dest='nb_competitors',
            type=int,
            default=4,
            help='Number of competitors in competition',
        )
        parser.add_argument(
            '--live_delay',
            dest='live_delay',
            type=int,
            default=15,
            help='Competition delay in seconds',
        )

    def handle(self, *args, **options):
        self.create_publisher()
        self.create_competition(options['live_delay'])
        self.create_competitors(options['nb_competitors'])
        self.stdout.write(u'Competition Started\n'
                          u'Press CTRL+C to stop')
        while True:
            try:
                self.update_competitors()
                time.sleep(self.competition.live_delay)
            except KeyboardInterrupt:
                break
        self.competition.delete()
        self.publisher.delete()

    def create_publisher(self):
        self.publisher = User.objects.create_user(
            u'Fake {}'.format(make_random_code(5))
        )

    def create_competition(self, live_delay):
        competition = Competition(
            publisher=self.publisher,
            name=u'Fake Live {}'.format(make_random_code(5)),
            live_delay=live_delay,
            latitude=62,
            longitude=22,
            zoom=12,
            publication_policy='public',
            signup_policy='closed',
            start_date=now(),
            end_date=now()+timedelta(3600*4),
            timezone='Europe/Helsinki',
        )
        competition.save()
        self.competition = competition

    def create_competitors(self, count):
        for ii in range(count):
            competitor = Competitor(
                competition=self.competition,
                name=u'Runner {} {}'.format(make_random_code(4), ii+1),
                short_name=u"R{}".format(ii+1),
                start_time=self.competition.start_date+timedelta(60*ii),
                approved=True,
            )
            competitor.save()

    def update_competitors(self):
        competitors = self.competition.approved_competitors.all()
        for ii, competitor in enumerate(competitors):
            time_offset = (now() - competitor.start_time).total_seconds()
            angle = (2 * math.pi * time_offset) / 300
            lon = 62 + .001 * (ii+1) * math.cos(angle)
            lat = 22 + .001 * (ii+1) * math.sin(angle)
            pos = GeoLocation(time.time(), [lat, lon])
            history = GeoLocationSeries([pos])
            route = Route(competitor=competitor, encoded_data=str(history))
            route.save()
