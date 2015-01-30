from django.test import TestCase
from seuranta.utils.geo import GeoLocation, GeoCoordinates, GeoLocationSeries
from decimal import Decimal


class SeurantaTestCase(TestCase):

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

    def test_init(self):
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
        s.union(GeoLocationSeries([GeoLocation(100000.9, [23, 67]), ]))
        self.assertEqual("`m}mlw@_|l_I_expAA??")