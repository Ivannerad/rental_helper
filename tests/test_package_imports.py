"""Minimal import smoke test for scaffold packages."""

from __future__ import annotations

import importlib
import unittest


class PackageImportTest(unittest.TestCase):
    def test_service_and_shared_packages_import(self) -> None:
        package_names = [
            "admin_bot",
            "userbot_worker",
            "chatbot_service",
            "shared",
            "shared.config",
            "shared.domain",
            "shared.queue",
            "shared.persistence",
            "shared.logging",
        ]

        for package_name in package_names:
            with self.subTest(package_name=package_name):
                importlib.import_module(package_name)


if __name__ == "__main__":
    unittest.main()
