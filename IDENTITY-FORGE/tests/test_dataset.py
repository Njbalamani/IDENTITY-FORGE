import csv
import shutil
import tempfile

from django.test import TestCase

from samples.generate_synthetic_dataset import generate_dataset, write_dataset


class SyntheticDatasetTests(TestCase):
    def test_dataset_is_deterministic_and_synthetic(self):
        first = generate_dataset(seed=7)
        second = generate_dataset(seed=7)
        self.assertEqual(first, second)
        self.assertTrue(all(user["username"].endswith(".invalid") for user in first["users"]))
        self.assertTrue(all(event["source"] == "SYNTHETIC" for event in first["events"]))

    def test_writer_creates_expected_csv_files(self):
        directory = tempfile.mkdtemp(prefix="identityforge-dataset-")
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        result = write_dataset(directory, seed=11)
        with (result / "access_events.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 360)
        self.assertIn("username", rows[0])
