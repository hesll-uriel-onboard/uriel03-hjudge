#import "config.typ": *
= Architecture Overview

#slide(title: [Summary])[
	#image("/assets/image.png")
]
#slide(title: [Summary])[
	Others:
	- Testing: Pytest + SQLite
	- Package manager: uv
]
#slide(title: [Constraints and Decisions])[
	1. Already-made decisions: Use the tech-stack currently use in Uriel, if known
		- Litestar for backend
		- DB: PostgreSQL + SQLAlchemy
			- Alembic for migration, not sure how Uriel is doing this
		- uv for package management and venv
		- Pytest + coverage for testing
	
	#pause
	2. Considering: how to fast-deliver?
		- Front-end: Jinja
		- Scheduler: Claude gave me solutions, I picked one: APScheduler
]
#slide(title: [Constraints and Decisions])[
	3. (goal) Split the LMS module and OJ module
		- "Uriel mình microservice till die"
		- can not deliver this yet due to time constraint
		- still, try to develop the two modules as independent as possible
]
