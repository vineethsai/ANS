# Agent Name Service (ANS) Tests

This directory contains tests for the Agent Name Service.

## Overview

The test suite covers various aspects of the ANS:

- Core functionality (agent registration, resolution, etc.)
- Database models and operations
- Cryptography functionality
- Protocol adapters
- API endpoints
- Configuration and environment validation
- Logging functionality

## Directory Structure

- `tests/`: Main test directory
  - `logs/`: Directory for log files generated during tests
  - `test_ans.py`: Core ANS functionality tests
  - `test_ans_name.py`: ANS name parsing and validation tests
  - `test_agent_registry.py`: Agent registry tests
  - `test_config.py`: Configuration and environment validation tests
  - `test_crypto.py`: Cryptography tests
  - `test_database.py`: Database functionality tests
  - `test_lifecycle.py`: Full agent lifecycle tests
  - `test_logging.py`: Logging functionality tests
  - `test_mcp_adapter.py`: MCP protocol adapter tests
  - `test_protocol_adapters.py`: Protocol adapter tests
  - `test_resolution.py`: Agent resolution tests
  - `test_security.py`: Security-related tests
  - `test_version_matching.py`: Version matching tests
  - `test_version_negotiation.py`: Version negotiation tests
  - `run_ans.py`: Script to run the ANS server for integration tests

## Running Tests

To run the entire test suite:

```bash
PYTHONPATH=/path/to/ANS pytest tests/
```

To run a specific test file:

```bash
PYTHONPATH=/path/to/ANS pytest tests/test_file.py
```

To run a specific test function:

```bash
PYTHONPATH=/path/to/ANS pytest tests/test_file.py::TestClass::test_function
```

## Test Database

Tests use a separate SQLite database located at `tests/logs/test_ans.db` to avoid interfering with any production data.

## Logs

All logs generated during tests are stored in the `tests/logs/` directory:

- `ans_server.log`: Server logs
- `ans_audit.log`: Security audit logs

## Adding New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for files and `test_*` for functions
2. Use pytest fixtures for setup/teardown
3. Ensure tests are independent and can run in any order
4. Use mocks for external dependencies
5. Add proper documentation

## Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test multiple components working together
- **Functional Tests**: Test the system from the user's perspective
- **Performance Tests**: Test system performance under load
- **Security Tests**: Test system security features

## Continuous Integration

These tests are run automatically on every pull request and push to the main branch.