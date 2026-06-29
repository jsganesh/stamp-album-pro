.PHONY: test run install dev clean

# Run the full test suite
test:
	venv/bin/python -m pytest src/tests/ -q

# Run the app in browser mode
run:
	venv/bin/python -m stamp_album --browser

# Install dependencies
install:
	pip install -e ".[dev]"

# Development mode with auto-reload
dev:
	STAMP_ALBUM_RELOAD=1 venv/bin/python -m stamp_album --browser

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache
	find src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
