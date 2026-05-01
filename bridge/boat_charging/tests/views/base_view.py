from bridge.boat_charging.views.base_view import BaseView
from core.tests.test_authentication import RespxActivatedAPITestCase


class BoatChargingTestCase(RespxActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.api_headers["access_token"] = (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTY4MTYxOTQsImV4cCI6MTc1NjgxOTc5NCwicm9sZXMiOlsiUk9MRV9VU0VSX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiZmlwczp0RmswZlJMUDA3WERLUll4YXU3TTJ6MUJ2djZGZmlLYUpsSjlLaDUtaW1nTlAtRWlEVHBVeW9JYXp0Vkc3YkNxdks2X1VhQWkxN2NhZjF1d3Z6NmFsQXBIZ2xobzVQdlJvWHpadDlFVlF6MjhTZ1U3c3F0TnU4WmR2QlFORUR2MHEwV0Z2OF9leG9FPSIsImxvY2FsZSI6Im5sLU5MIn0.HatOyxHBqFjYXRb1DfaPWVZGwN3RQ3R_BTZEmKqge6eonxaDLgBCBMTUwaKppj7DtnLII4-DkIzKxj-LeP0sfMkqlpFoQKJTMPX2bidZr0_FwlQ7Dm1Mxd284EQqx132HK0Xke4jjqXxE7elR7iZYDjnDoYnXl85PkjEBMcYsSHRj0ibWvH1ChkGyXpEgfwCy4uqQYRM7iOF3-A6dvgV5ti9kSkcxP5IK_7Z7SRDuhbxMEdL_ON3eJdErs7HraxGowL_HlncKnwSZO82KHObUKpZeLvdSA4CHAiCmnyFlunCMOsH5hWM99ys00rEEMvha3AsXFhLTm5uRmmoA2nwvCR5BR4tu3olhm0NG9PAuWny2rmbCrFtz739-WOX1lzP6Xxuo6cC4lU_gy2AkI3QYtQ2Hj-rRQ-3peZcBpQ49nS-VNCnrMjLo6S2BW4I6SYamN3-0mhqFSnyUZ9YiQbwaLhmJJqXzou-kFuvtY6OX_afm5deh8CfFUO03O6C0bVJ-8oSC61QAEIEdNaJR0Vb2dqAM9qAJWPP-SNr_dqte9eCV05POf0XT0ZkjtHmrM678fzIjE-tGJSN-LrumrYXZU8zVTqNBw57sDhuUROhQLDSeqoLbKJHkoQYSFIMWlouhanAegSuHFzZRmb8SkHhZ0bLyUZkFM9Rvozy21M2YKU"
        )


class TestBaseView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.view = BaseView()

    def test_convert_regular_hours(self):
        regular_hours = (
            [
                {"weekday": 1, "periodBegin": "08:00", "periodEnd": "18:00"},
                {"weekday": 2, "periodBegin": "08:00", "periodEnd": "18:00"},
                {"weekday": 3, "periodBegin": "09:00", "periodEnd": "19:30"},
                {"weekday": 4, "periodBegin": "04:12", "periodEnd": "08:12"},
                {"weekday": 5, "periodBegin": "07:12", "periodEnd": "13:12"},
                {"weekday": 6, "periodBegin": "08:12", "periodEnd": "21:12"},
                {"weekday": 7, "periodBegin": "07:19", "periodEnd": "08:19"},
            ],
        )
        converted_hours = self.view._convert_regular_hours(regular_hours)
        expected_converted_hours = [
            {
                "dayOfWeek": 1,
                "opening": {"hours": 8, "minutes": 0},
                "closing": {"hours": 18, "minutes": 0},
            },
            {
                "dayOfWeek": 2,
                "opening": {"hours": 8, "minutes": 0},
                "closing": {"hours": 18, "minutes": 0},
            },
            {
                "dayOfWeek": 3,
                "opening": {"hours": 9, "minutes": 0},
                "closing": {"hours": 19, "minutes": 30},
            },
            {
                "dayOfWeek": 4,
                "opening": {"hours": 4, "minutes": 12},
                "closing": {"hours": 8, "minutes": 12},
            },
            {
                "dayOfWeek": 5,
                "opening": {"hours": 7, "minutes": 12},
                "closing": {"hours": 13, "minutes": 12},
            },
            {
                "dayOfWeek": 6,
                "opening": {"hours": 8, "minutes": 12},
                "closing": {"hours": 21, "minutes": 12},
            },
            {
                "dayOfWeek": 0,
                "opening": {"hours": 7, "minutes": 19},
                "closing": {"hours": 8, "minutes": 19},
            },
        ]
        self.assertEqual(converted_hours, expected_converted_hours)

    def test_get_addr(self):
        input_str = "Tilanusstraat 10-2"
        street, number = BaseView.split_address(input_str)
        self.assertEqual(street, "Tilanusstraat ")
        self.assertEqual(number, "10-2")

    def test_get_addr_2(self):
        input_str = "Amstel 1"
        street, number = BaseView.split_address(input_str)
        self.assertEqual(street, "Amstel ")
        self.assertEqual(number, "1")

    def test_get_addr_3(self):
        input_str = "Retief Straat 15h/2"
        street, number = BaseView.split_address(input_str)
        self.assertEqual(street, "Retief Straat ")
        self.assertEqual(number, "15h/2")

    def test_get_addr4(self):
        input_str = "Main Street 12 bis"
        street, number = BaseView.split_address(input_str)
        self.assertEqual(street, "Main Street ")
        self.assertEqual(number, "12 bis")

    def test_get_addr5(self):
        input_str = "Kraanspoor 7L3"
        street, number = BaseView.split_address(input_str)
        self.assertEqual(street, "Kraanspoor ")
        self.assertEqual(number, "7L3")
