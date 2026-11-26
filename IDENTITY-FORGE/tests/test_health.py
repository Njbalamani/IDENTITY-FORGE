from django.core.management import call_command
from django.test import TestCase

from tests.factories import create_organization, create_user


class HealthCommandTests(TestCase):
    def test_health_command_passes(self):
        organization = create_organization()
        create_user(organization, "health@example.invalid")
        call_command("identityforge_health")
