# Rilato Tests

This directory contains tests for the Rilato application.

## Test Structure

The tests are organized to mirror the structure of the `src` directory:

- `test_main.py` - Tests for the main application class and entry point
- Additional test files will be added as the application grows

## Running Tests

To run all tests:

```bash
pytest
```

To run specific tests:

```bash
pytest tests/test_main.py
```

## Test Categories

Tests are categorized using markers:

- `@pytest.mark.gtk` - Tests that require GTK
- `@pytest.mark.slow` - Tests that are slow to run

To run tests excluding a category:

```bash
pytest -m "not gtk"
pytest -m "not slow"
```

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `mock_window` - A mock window for testing
- `mock_application` - A mock application for testing
- `gtk_main_loop` - A GLib main loop for testing asynchronous operations

## Adding New Tests

When adding new tests:

1. Create a new test file named `test_<module_name>.py`
2. Import the module to test
3. Create test classes and functions following the naming convention
4. Use appropriate fixtures from `conftest.py`
5. Add appropriate markers for categorization