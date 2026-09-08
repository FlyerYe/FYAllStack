import unittest
from dataclasses import replace

from app.db.migrate import _validate_checksums, load_migrations


class MigrationDefinitionTests(unittest.TestCase):
    def test_migrations_are_versioned_and_sorted(self):
        migrations = load_migrations()
        self.assertTrue(migrations)
        self.assertEqual(
            [migration.version for migration in migrations],
            sorted(migration.version for migration in migrations),
        )
        self.assertEqual(migrations[0].version, "V001")
        self.assertEqual(len(migrations[0].checksum), 64)
        self.assertIn("ALTER TABLE users", migrations[0].sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS orders", migrations[0].sql)

    def test_checksum_drift_is_rejected(self):
        migration = load_migrations()[0]
        changed = replace(migration, checksum="0" * 64)

        with self.assertRaisesRegex(RuntimeError, "checksum 不匹配"):
            _validate_checksums([migration], {changed.version: changed.checksum})


if __name__ == "__main__":
    unittest.main()
