#!/bin/bash

# Run Open Trader Test Suite
# Usage: ./run_tests.sh [unit|integration|all|coverage]

set -e

cd "$(dirname "$0")/backend"

MODE=${1:-all}

echo "🧪 Open Trader Test Suite"
echo "=========================="
echo ""

case $MODE in
    unit)
        echo "Running unit tests only..."
        pytest tests/ -v -m "unit"
        ;;
    integration)
        echo "Running integration tests..."
        pytest tests/ -v -m "integration"
        ;;
    coverage)
        echo "Running all tests with coverage..."
        pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo "📊 Coverage report generated in: backend/htmlcov/index.html"
        ;;
    all|*)
        echo "Running all tests..."
        pytest tests/ -v
        ;;
esac

echo ""
echo "✅ Tests complete!"