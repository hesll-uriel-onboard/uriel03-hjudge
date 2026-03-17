COMMAND=uv run --env-file=.creds/.env

test:
	${COMMAND} pytest

run:
	${COMMAND} litestar --app hjudge.app:app run --host 0.0.0.0

debug:
	${COMMAND} litestar --app hjudge.app:app run --debug --host 0.0.0.0

coverage:
	${COMMAND} coverage run -m pytest
	${COMMAND} coverage report --fail-under=80

new-migrations:
	${COMMAND} python migrations/new-version.py -m "${MSG}"

migrate:
	${COMMAND} alembic upgrade head
