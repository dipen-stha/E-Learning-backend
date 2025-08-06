format:
	black .
	ruff check . --fix

lint:
	ruff check .