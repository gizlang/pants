# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_sources()

python_tests(
    name="test",
    overrides={
        "rules_integration_test.py": dict(
            dependencies=[":package_lock_json"],
        ),
    },
)

# The package.json file is inlined in ./rules_integration_tests.py
resource(name="package_lock_json", source="package-lock.json")
