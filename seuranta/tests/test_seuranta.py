# coding=utf-8
from decimal import Decimal
import uuid
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
import time
from seuranta.models import BLANK_GIF_B64
from seuranta.utils.b64_codec import url_safe_b64_codec, B64Codec
from seuranta.utils.geo import GeoLocation, GeoCoordinates, GeoLocationSeries
from seuranta.utils.validators import validate_longitude, validate_latitude, \
    validate_nice_slug


class ApiTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@aol.com',
                                             'passw0rd!')
        self.user_b = User.objects.create_user('bob', 'bob@bing.com',
                                               'L3tmeIn')
        self.basic_competition_data = {
            'name': 'Jukola 2015',
            'live_delay': 30,
            'latitude': 62,
            'longitude': 22,
            'zoom': 12,
            'publication_policy': 'public',
            'signup_policy': 'closed',
            'start_date': '2015-06-17T23:00',
            'end_date': '2015-06-18T12:00',
            'timezone': 'Europe/Helsinki',
        }
        self.basic_competitor_data = {
            'name': 'Kapteeni Kiila',
            'short_name': 'KK',
            'access_code': '12345',
            'approved': True,
        }

    def test_api_time(self):
        client = APIClient()
        url = reverse('seuranta_api_time')
        t0 = time.time()
        response = client.get(url, format='json')
        t1 = time.time()
        ts = response.data['time']
        self.assertTrue(t0 < response.data['time'] < t1)
        self.assertAlmostEqual(t0, ts, places=1)
        self.assertAlmostEqual(t1, ts, places=1)

    def test_api_token(self):
        """
        Create a token for an user void it and create another one,
        ensure new token is different
        """
        client = APIClient()
        url = reverse('seuranta_api_auth_token_obtain')
        destroy_url = reverse('seuranta_api_auth_token_destroy')
        response = client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = client.post(
            destroy_url,
            {'username': 'alice', 'password': 'passw0rd!'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = client.post(
            url,
            {'username': 'alice', 'password': 'passw0rd!'},
            format='json'
        )
        del_resp = client.post(
            destroy_url,
            {'username': 'alice', 'password': 'passw0rd!'},
            format='json'
        )
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        response2 = client.post(
            url,
            {'username': 'alice', 'password': 'passw0rd!'},
            format='json'
        )
        self.assertTrue(response.data['token'] != response2.data['token'])

    def test_create_public_competition(self):
        """
        Test creating and listing public competition
        """
        client = APIClient()
        url = reverse('seuranta_api_competitions')
        data = self.basic_competition_data
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        client.login(username='alice', password='passw0rd!')
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        competition_id = response.data['id']
        client.logout()
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        map_url = reverse(
            'seuranta_api_competition_map_download',
            kwargs={'pk': competition_id},
        )
        response = client.get(map_url, format='json')
        # Competition not started 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Create a competition in past
        data2 = self.basic_competition_data
        data2['name'] = 'Jukola 2014'
        data2['start_date'] = '2014-06-17T23:00'
        data2['end_date'] = '2014-06-18T12:00'
        client.login(username='alice', password='passw0rd!')
        response = client.post(url, data2, format='json')
        client.logout()
        competition_id2 = response.data['id']
        map_url = reverse(
            'seuranta_api_competition_map_download',
            kwargs={'pk': competition_id2},
        )
        map_api_url = reverse(
            'seuranta_api_competition_map',
            kwargs={'pk': competition_id2},
        )
        response = client.get(map_api_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = client.get(map_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.encode('base64').strip(),
                         BLANK_GIF_B64)
        response = client.get(
            url,
            {'id': competition_id},
            format='json'
        )
        self.assertEqual(response.data['count'], 1)
        response = client.get(
            url,
            {
                'id[]': [competition_id, competition_id2]
            },
            format='json'
        )
        self.assertEqual(response.data['count'], 2)
        response = client.get(
            url,
            {
                'reverse_order': 'true'
            },
            format='json'
        )
        self.assertEqual(response.data['results'][0]['id'], competition_id2)
        response = client.get(
            url,
            {
                'reverse_order': 'banana'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_secret_competition(self):
        """
        Test creating and listing public competition
        """
        client = APIClient()
        url = reverse('seuranta_api_competitions')
        data = self.basic_competition_data
        data['publication_policy'] = 'secret'
        client.login(username='alice', password='passw0rd!')
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = client.get(url, format='json')
        self.assertEqual(response.data['count'], 1)
        client.logout()
        response = client.get(url, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_create_private_competition(self):
        """
        Test creating and listing private competition
        """
        client = APIClient()
        url = reverse('seuranta_api_competitions')
        data = self.basic_competition_data
        data['publication_policy'] = 'private'
        client.login(username='alice', password='passw0rd!')
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = client.get(url, format='json')
        self.assertEqual(response.data['count'], 1)
        client.logout()
        response = client.get(url, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_competitor_token(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        url_api_token = reverse('seuranta_api_obtain_competitor_token')
        url_destroy_api_token = reverse(
            'seuranta_api_destroy_competitor_token'
        )
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        competitor_id = response.data['id']
        access_code = self.basic_competitor_data['access_code']
        client.logout()
        cred = {
            'competitor': competitor_id,
            'access_code': access_code,
        }
        response = client.post(url_destroy_api_token,  cred,  format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = client.post(url_api_token, cred, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pub_token1 = response.data['token']
        response = client.post(url_destroy_api_token,  cred,  format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = client.post(url_api_token, cred, format='json')
        pub_token2 = response.data['token']
        self.assertTrue(pub_token1 != pub_token2)

    def test_edit_competitor(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        url_api_competitor_token = reverse(
            'seuranta_api_obtain_competitor_token'
        )
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        competitor_id = response.data['id']
        access_code = self.basic_competitor_data['access_code']
        client.logout()
        cred = {
            'competitor': competitor_id,
            'access_code': access_code,
        }
        response = client.post(url_api_competitor_token, cred, format='json')
        competitor_token = response.data['token']
        url_api_competitor = reverse(
            'seuranta_api_competitor',
            kwargs={'pk': competitor_id}
        )
        response = client.patch(
            url_api_competitor,
            {'name': 'Bob Marcel',
             'token': competitor_token},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_create_competitor_in_closed_competition(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        client.logout()
        # logged out, this competition is not a valid option anymore,
        #  hence return bad request
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = client.get(url_api_competitor, format='json')
        self.assertEqual(response.data['count'], 1)

    def test_create_competitor_in_org_val_competition(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        competition_data['signup_policy'] = 'org_val'
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['approved'])
        client.logout()
        # logged out, this competitor wont be approved right away
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['approved'])

    def test_create_competitor_in_open_competition(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        competition_data['signup_policy'] = 'open'
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['approved'])
        client.logout()
        # logged out, everything goes!
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['approved'])

    def test_publish_route(self):
        url_api_competition = reverse('seuranta_api_competitions')
        url_api_competitor = reverse('seuranta_api_competitors')
        client = APIClient()
        client.login(username='alice', password='passw0rd!')
        competition_data = self.basic_competition_data
        response = client.post(url_api_competition, competition_data,
                               format='json')
        competition_id = response.data['id']
        competitor_data = self.basic_competitor_data
        competitor_data['competition'] = competition_id
        response = client.post(url_api_competitor, competitor_data,
                               format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        competitor_id = response.data['id']
        client.logout()
        response = client.post(
            reverse('seuranta_api_obtain_competitor_token'),
            {
                'competitor': competitor_id,
                'access_code': competitor_data['access_code']
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pub_token = response.data['token']
        response = client.post(
            reverse('seuranta_api_routes'),
            {
                'competitor': competitor_id,
                'encoded_data': 'A??',
                'token': pub_token,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        client.post(
            reverse('seuranta_api_routes'),
            {
                'competitor': competitor_id,
                'encoded_data': 'CAA',
                'token': pub_token,
            }
        )
        response = client.get(reverse('seuranta_api_routes'), format='json')
        self.assertEqual(response.data['count'], 2)
        response = client.get(
            reverse('seuranta_api_competitor_route',
                    kwargs={'pk': competitor_id}),
            format='json'
        )
        self.assertEqual(response.data['encoded_data'], 'A??AAA')


class ValidatorsTestCase(TestCase):
    def test_lat_lon_validator(self):
        with self.assertRaises(ValidationError):
            validate_longitude(-180.00001)
        with self.assertRaises(ValidationError):
            validate_longitude(-180.00001)
        with self.assertRaises(ValidationError):
            validate_latitude(90.00001)
        with self.assertRaises(ValidationError):
            validate_latitude(-90.00001)

    def test_nice_slug(self):
        for slug in ('_hello', 'hello_', 'héllo', 'hello_-world', 'hei',
                     'this_is_way_too_long_to_be_a_slug'):
            with self.assertRaises(ValidationError):
                validate_nice_slug(slug)


class B64CodecTestCase(TestCase):
    def test_symmetry(self):
        original = uuid.uuid4().bytes
        encoded = url_safe_b64_codec.encode(original)
        decoded = url_safe_b64_codec.decode(encoded)
        self.assertEqual(original, decoded)

    def test_original(self):
        with self.assertRaises(TypeError):
            bad_codec = B64Codec('banana')
        b64_codec = B64Codec()
        original = uuid.uuid4().bytes
        encoded = b64_codec.encode(original)
        decoded = b64_codec.decode(encoded)
        self.assertEqual(original, decoded)


class GeoToolTestCase(TestCase):

    def setUp(self):
        self.valid_lat_lon_str = '61.4682694,23.7594638'
        self.valid_lat_float = 61.4682694
        self.valid_lon_float = 23.7594638
        self.valid_lat_str = '61.4682694'
        self.valid_lon_str = '23.7594638'
        self.valid_lat_dec = Decimal('61.4682694')
        self.valid_lon_dec = Decimal('23.7594638')
        self.valid_lat_neg = '-23.977849'
        self.valid_lon_neg = '-123.977849'
        self.invalid_lon_overflow = '190.35'
        self.expected_lon_overflow = '-169.65'
        self.invalid_lat_overflow = '92.35'
        self.expected_lat_overflow = '87.65'

    def test_geo(self):
        gp1 = GeoCoordinates(self.valid_lat_lon_str)
        gp2 = GeoCoordinates(self.valid_lat_str, self.valid_lon_str)
        gp3 = GeoCoordinates(self.valid_lat_dec, self.valid_lon_dec)
        gp4 = GeoCoordinates(self.valid_lat_float, self.valid_lon_float)
        gp5 = GeoCoordinates([self.valid_lat_str, self.valid_lon_str])
        gp6 = GeoCoordinates([self.valid_lat_dec, self.valid_lon_dec])
        gp7 = GeoCoordinates([self.valid_lat_float, self.valid_lon_float])
        gp8 = GeoCoordinates(self.valid_lat_neg, self.valid_lon_neg)
        gp8.latitude = self.valid_lat_str
        gp8.longitude = self.valid_lon_dec
        self.assertEqual(gp1.latitude, self.valid_lat_dec)
        self.assertEqual(gp1.longitude, self.valid_lon_dec)
        self.assertEqual(gp1, gp2)
        self.assertEqual(gp1, gp3)
        self.assertEqual(gp1, gp4)
        self.assertEqual(gp1, gp5)
        self.assertEqual(gp1, gp6)
        self.assertEqual(gp1, gp7)
        self.assertEqual(gp1, gp8)
        tgl = GeoLocation(Decimal('99999.9'),
                          (Decimal('52.5'), Decimal('13.4')))
        tgl2 = GeoLocation(Decimal('99999.9'),
                           GeoCoordinates(Decimal('52.5'),
                                          Decimal('13.4')))
        tgl3 = GeoLocation(Decimal('99998.9'),
                           GeoCoordinates(Decimal('52.5'),
                                          Decimal('13.4')))
        self.assertEqual(tgl.timestamp, Decimal('99999.9'))
        self.assertEqual(tgl.coordinates.latitude, Decimal('52.5'))
        self.assertEqual(tgl.coordinates.longitude, Decimal('13.4'))
        self.assertEqual(tgl, tgl2)
        self.assertNotEqual(tgl, tgl3)
        self.assertTrue(tgl > tgl3)
        s = GeoLocationSeries([tgl, tgl3])
        joined_route = s.union(
            GeoLocationSeries([GeoLocation(100000.9, [23, 67]), ])
        )
        self.assertEqual("`m}mlw@_|l_I_expAA??A~u`sD_wcfI",
                         str(joined_route))