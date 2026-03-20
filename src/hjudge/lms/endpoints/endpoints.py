from hjudge.lms.endpoints.backend import course as backend_course
from hjudge.lms.endpoints.backend import dashboard as backend_dashboard
from hjudge.lms.endpoints.backend import user as backend_user
from hjudge.lms.endpoints.frontend import course as frontend_course
from hjudge.lms.endpoints.frontend import user as frontend_user

lms_endpoints = [
    backend_user.login,
    backend_user.logout,
    backend_user.register,
    backend_course.create_course,
    backend_course.list_courses,
    backend_course.get_course,
    backend_course.update_course,
    backend_course.create_lesson,
    backend_course.list_lessons,
    backend_course.get_lesson,
    backend_course.update_lesson,
    backend_course.add_admin,
    backend_course.remove_admin,
    backend_dashboard.get_lesson_progress,
    backend_dashboard.get_lesson_leaderboard,
    backend_dashboard.get_course_progress,
    backend_dashboard.get_course_leaderboard,
    frontend_user.home,
    frontend_user.register,
    frontend_user.login,
    frontend_user.profile,
    frontend_course.courses_page,
    frontend_course.new_course_page,
    frontend_course.edit_course_page,
    frontend_course.course_detail_page,
    frontend_course.new_lesson_page,
    frontend_course.edit_lesson_page,
    frontend_course.lesson_detail_page,
]
