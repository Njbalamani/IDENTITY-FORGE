from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        throttling = patch.object(AnonRateThrottle, "THROTTLE_RATES", {"anon": "2/min"})
        throttling.start()
        self.addCleanup(throttling.stop)
        self.client = APIClient()

    def test_repeated_anonymous_token_requests_are_throttled(self):
        payload = {"username": "unknown@example.invalid", "password": "wrong-password"}
        responses = [self.client.post("/api/auth/token/", payload, format="json") for _ in range(3)]
        self.assertEqual([response.status_code for response in responses[:2]], [401, 401])
        self.assertEqual(responses[2].status_code, status.HTTP_429_TOO_MANY_REQUESTS)
