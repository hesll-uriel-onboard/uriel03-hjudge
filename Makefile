test:
	uv run pytest

run:
	uv run litestar --app hjudge.app:app run

debug:
	uv run litestar --app hjudge.app:app run

coverage:
	uv run coverage run -m pytest
	uv run coverage report --fail-under=80
