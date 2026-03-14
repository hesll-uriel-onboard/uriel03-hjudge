# HJudge Project

An Online Judge web application built with Litestar (Python) and Jinja2 templates.

## Tech Stack

- **Backend**: Litestar (Python async web framework)
- **Database**: PostgreSQL with SQLAlchemy
- **Templates**: Jinja2
- **Styling**: Tailwind CSS (via CDN)
- **Migrations**: Alembic

## Common Commands

```bash
# Run the development server
make run
# Or with custom port:
uv run litestar --app hjudge.app:app run --port 8080

# Run with debug mode
make debug

# Run tests
make test

# Run migrations
make migrate

# Create new migration
make new-migrations MSG="your message"
```

## Project Structure

```
src/hjudge/
├── app.py                    # Litestar app entry point
├── templates/
│   ├── base.jinja           # Base template with layout
│   ├── components/          # Reusable template components
│   │   ├── header.jinja     # Navigation bar
│   │   ├── footer.jinja     # Footer
│   │   ├── spinner.jinja    # Loading spinner SVG
│   │   └── form_macros.jinja # Form macros (auth_form, input)
│   └── views/               # Page templates
│       ├── home.jinja
│       ├── login.jinja
│       ├── register.jinja
│       └── exercises.jinja
├── lms/                     # Learning Management System module
│   ├── models/              # Domain models
│   ├── db/                  # Database entities & repositories
│   ├── services/            # Business logic
│   └── endpoints/           # HTTP handlers
│       ├── backend/         # API endpoints
│       └── frontend/        # Page handlers
└── oj/                      # Online Judge module
    ├── models/              # Domain models (Exercise, Submission)
    ├── db/                  # Database entities & repositories
    ├── services/            # Business logic
    └── endpoints/           # HTTP handlers
```

## API Endpoints

### Authentication
- `POST /api/login` - User login (returns session cookie)
- `POST /api/register` - User registration

### Exercises
- `GET /api/exercises?judge={judge}&code={code}` - Check exercise existence
- `GET /exercises` - Exercise list page

### Submissions
- `GET /api/submissions?user={user_id}&exercise={exercise_id}` - Get submissions
- `POST /api/submissions/` - Create submission (body: user_id, exercise_id, verdict)

## Frontend Patterns

### Template Inheritance
All page templates extend `base.jinja`:
```jinja
{% extends "base.jinja" %}
{% block content %}
    ...
{% endblock %}
```

### User Authentication Check
Templates have access to `user` context variable:
```jinja
{% if (user is defined) and not(user == none) %}
    <!-- Logged in -->
{% else %}
    <!-- Not logged in -->
{% endif %}
```

### Form Macros
Use the shared macros for auth forms:
```jinja
{% from "components/form_macros.jinja" import auth_form, input %}
{% call auth_form(title, subtitle, link, btn_text, btn_loading_text) %}
    {{ input("id", "Label", "type", "placeholder") }}
{% endcall %}
```

## Code Style

- Python: Follow PEP 8, use `ruff` for linting
- Templates: 4-space indentation, whitespace around Jinja tags
- JavaScript: Use `async/await`, avoid `then()` chains

## Notes

- Tailwind CSS is loaded via CDN for development. For production, consider setting up a build process with purging.
- The app uses cookie-based session authentication. The cookie name is defined in `COOKIE_KEY` constant.
- Judge integrations (e.g., Codeforces) are in `oj/models/judges/`.

## Lessons Learned

### Soft Delete Over Hard Delete
The `UserSession.active` column was already designed for session deactivation. Use it instead of deleting rows - preserves audit trail and matches existing architecture.

### `required=False` for Public Pages
When calling `authenticate_user()` in frontend endpoints that should work for both logged-in and anonymous users (like `/` and `/exercises`), always pass `required=False`. Otherwise, an inactive/invalid session causes `NotAuthorizedError` which results in 500 errors.

### Cookie Clearing Needs `max_age=0`
Setting an empty cookie value alone doesn't clear it in the browser. Must set `max_age=0` (or an expired date) for the browser to actually delete the cookie.

### Empty Response Body Breaks `response.json()`
If an endpoint returns 200 OK with an empty body, calling `response.json()` will throw an error. Only parse JSON when needed (e.g., error cases). On success, just redirect without parsing.

### Register New Endpoints
After creating a new endpoint handler, remember to add it to the endpoint list (e.g., `lms_endpoints` in `lms/endpoints/endpoints.py`). Otherwise it returns 404.

### Grep for All Usages
When fixing an issue in one place, immediately grep for all other usages to find similar issues (e.g., when fixing `authenticate_user` call in one endpoint, check all other endpoints too).