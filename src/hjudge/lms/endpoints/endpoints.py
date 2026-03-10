from hjudge.lms.endpoints.backend import user as backend
from hjudge.lms.endpoints.frontend import user as frontend

lms_endpoints = [
    backend.login,
    backend.register,
    frontend.home,
    frontend.register,
    frontend.login
]
