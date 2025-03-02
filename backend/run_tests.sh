#!/bin/bash

# Run unit tests only
run_unit_tests() {
  echo "Running unit tests..."
  python -m pytest tests/unit
}

# Run integration tests only 
run_integration_tests() {
  echo "Running integration tests..."
  python -m pytest tests/integration
}

# Run all tests
run_all_tests() {
  echo "Running all tests..."
  python -m pytest
}

# Main logic
case "$1" in
  unit)
    run_unit_tests
    ;;
  integration)
    run_integration_tests
    ;;
  *)
    run_all_tests
    ;;
esac