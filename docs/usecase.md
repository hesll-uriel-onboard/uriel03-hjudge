# HJudge Use Case Document

This document describes the business use cases implemented in the HJudge application's services layer.

## Table of Contents

- [LMS Module](#lms-module-learning-management-system)
  - [Authentication](#authentication)
  - [Course Management](#course-management)
  - [Lesson Management](#lesson-management)
  - [Course Administration](#course-administration)
- [OJ Module](#oj-module-online-judge)
  - [Exercise Management](#exercise-management)
  - [Submission Management](#submission-management)
  - [User Judge Management](#user-judge-management)
  - [Crawling](#crawling)

---

## LMS Module (Learning Management System)

### Authentication

#### UC-LMS-001: Register

**Description:** Create a new user account.

**Actor:** Anonymous user

**Preconditions:**
- Username is not already registered

**Main Flow:**
1. User provides username, password, and name
2. System checks if username already exists
3. System creates user with hashed password
4. System automatically logs user in (creates active session)
5. System returns User model

**Business Rules:**
- Passwords are hashed before storage
- User is automatically logged in after registration (session created)
- Username must be unique (raises `UserExistedError` if duplicate)

**Errors:**
- `UserExistedError` (409 Conflict): Username already registered

---

#### UC-LMS-002: Login

**Description:** Authenticate user and create session.

**Actor:** Registered user

**Preconditions:**
- User account exists with the provided username

**Main Flow:**
1. User provides username and password
2. System retrieves user by username
3. System verifies password against stored hash
4. System creates new session with unique cookie
5. System returns UserSession model

**Business Rules:**
- Passwords are hashed and compared securely
- Each login creates a new session
- Sessions have unique cookie identifiers

**Errors:**
- `UserNotFoundError` (400 Bad Request): Username not found (message: "Wrong credentials.")
- `UserWrongPasswordError` (400 Bad Request): Password incorrect (message: "Wrong credentials.")

---

#### UC-LMS-003: Logout

**Description:** Deactivate user session.

**Actor:** Authenticated user

**Preconditions:**
- User has an active session

**Main Flow:**
1. User provides session cookie
2. System deactivates the session (sets `active = false`)
3. Session is soft-deleted (not removed from database)

**Business Rules:**
- Uses soft delete pattern (sets `active = false` rather than deleting)
- Preserves audit trail of sessions

---

### Course Management

#### UC-LMS-004: Create Course

**Description:** Create a new course.

**Actor:** Authenticated user

**Preconditions:**
- Course slug is not already used

**Main Flow:**
1. User provides title, content, and slug
2. System checks slug uniqueness
3. System creates course
4. System makes creator the first admin
5. System returns Course model

**Business Rules:**
- Course creator automatically becomes course admin
- Slug must be globally unique across all courses

**Errors:**
- `CourseSlugExistsError` (409 Conflict): Slug already exists

---

#### UC-LMS-005: Update Course

**Description:** Update course details.

**Actor:** Course admin

**Preconditions:**
- Course exists
- User is a course admin

**Main Flow:**
1. User provides course ID, new title, and new content
2. System verifies user is course admin
3. System updates course fields
4. System returns updated Course model

**Business Rules:**
- Only course admins can update course details
- Slug cannot be changed after creation

**Errors:**
- `NotCourseAdminError` (401 Unauthorized): User is not admin
- `CourseNotFoundError` (400 Bad Request): Course does not exist

---

#### UC-LMS-006: Get Course

**Description:** Retrieve a course by ID.

**Actor:** Any user (authenticated or anonymous)

**Preconditions:** None

**Main Flow:**
1. User provides course ID
2. System retrieves course from database
3. System returns Course model or None

**Business Rules:**
- No authentication required to view courses

---

#### UC-LMS-007: Get Course by Slug

**Description:** Retrieve a course by slug.

**Actor:** Any user (authenticated or anonymous)

**Preconditions:** None

**Main Flow:**
1. User provides course slug
2. System retrieves course from database
3. System returns Course model or None

**Business Rules:**
- No authentication required to view courses
- Slug lookup is case-sensitive

---

#### UC-LMS-008: List Courses

**Description:** List all courses.

**Actor:** Any user (authenticated or anonymous)

**Preconditions:** None

**Main Flow:**
1. System retrieves all courses
2. System returns list of Course models

**Business Rules:**
- No authentication required
- Returns all courses (no pagination currently implemented)

---

### Lesson Management

#### UC-LMS-009: Create Lesson

**Description:** Create a lesson within a course.

**Actor:** Course admin

**Preconditions:**
- Course exists
- User is course admin
- Lesson slug is unique within the course

**Main Flow:**
1. User provides course ID, title, content, slug, and exercise IDs
2. System verifies user is course admin
3. System verifies course exists
4. System checks slug uniqueness within course
5. System assigns next order number
6. System creates lesson
7. System returns Lesson model

**Business Rules:**
- Lesson slug must be unique within a course (not globally)
- Order is automatically assigned (next available number)
- Exercise IDs are stored as string UUIDs

**Errors:**
- `NotCourseAdminError` (401 Unauthorized): User is not admin
- `CourseNotFoundError` (400 Bad Request): Course does not exist
- `LessonSlugExistsError` (409 Conflict): Slug already exists in course

---

#### UC-LMS-010: Update Lesson

**Description:** Update lesson details.

**Actor:** Course admin

**Preconditions:**
- Lesson exists
- User is course admin

**Main Flow:**
1. User provides lesson ID, new title, new content, and new exercise IDs
2. System retrieves lesson
3. System verifies user is admin of lesson's course
4. System updates lesson fields
5. System returns updated Lesson model

**Business Rules:**
- Only course admins can update lessons
- Title, content, and exercise IDs can be updated
- Slug and order cannot be changed after creation

**Errors:**
- `NotCourseAdminError` (401 Unauthorized): User is not admin
- `CourseNotFoundError` (400 Bad Request): Lesson does not exist

---

#### UC-LMS-011: Get Lesson by Slug

**Description:** Retrieve a lesson by course slug and lesson slug.

**Actor:** Any user (authenticated or anonymous)

**Preconditions:** None

**Main Flow:**
1. User provides course slug and lesson slug
2. System retrieves lesson
3. System returns Lesson model or None

**Business Rules:**
- No authentication required to view lessons
- Lesson identified by composite key (course slug + lesson slug)

---

#### UC-LMS-012: List Lessons

**Description:** List all lessons in a course.

**Actor:** Any user (authenticated or anonymous)

**Preconditions:** None

**Main Flow:**
1. User provides course ID
2. System retrieves all lessons for course
3. System returns list of Lesson models ordered by `order` field

**Business Rules:**
- No authentication required
- Lessons returned in order sequence

---

### Course Administration

#### UC-LMS-013: Add Course Admin

**Description:** Add a new admin to a course.

**Actor:** Course admin

**Preconditions:**
- Requester is course admin
- New admin user exists

**Main Flow:**
1. Requester provides course ID and new admin's user ID
2. System verifies requester is course admin
3. System adds new admin
4. Transaction committed

**Business Rules:**
- Only existing admins can add new admins
- Same user can be added multiple times (idempotent due to unique constraint)

**Errors:**
- `NotCourseAdminError` (401 Unauthorized): Requester is not admin

---

#### UC-LMS-014: Remove Course Admin

**Description:** Remove an admin from a course.

**Actor:** Course admin

**Preconditions:**
- Requester is course admin
- Course has more than one admin

**Main Flow:**
1. Requester provides course ID and admin's user ID to remove
2. System verifies requester is course admin
3. System checks course has more than one admin
4. System removes admin
5. Transaction committed

**Business Rules:**
- Cannot remove the last admin (prevents orphan courses)
- Admin can remove themselves or other admins

**Errors:**
- `NotCourseAdminError` (401 Unauthorized): Requester is not admin
- `CannotRemoveLastAdminError` (400 Bad Request): Would leave course without admins

---

#### UC-LMS-015: Check Admin Status

**Description:** Check if a user is an admin of a course.

**Actor:** System (internal use)

**Preconditions:** None

**Main Flow:**
1. System provides course ID and user ID
2. System queries admin relationship
3. Returns boolean

**Business Rules:**
- Used internally for authorization checks

---

## OJ Module (Online Judge)

### Exercise Management

#### UC-OJ-001: Check Exercise Existence

**Description:** Check if an exercise exists; auto-crawl if not found.

**Actor:** Authenticated user

**Preconditions:** None

**Main Flow:**
1. User provides judge name and exercise code
2. System checks if exercise exists in database
3. If found, returns Exercise model immediately
4. If not found, system attempts to crawl from external judge
5. System stores crawled exercises in database
6. System re-checks for the specific exercise
7. Returns Exercise model or None if still not found

**Business Rules:**
- Auto-crawls batch of exercises starting from requested exercise code
- Crawl may find multiple exercises, all stored in database
- Returns None only if exercise not found after crawl attempt

**Errors:**
- `JudgeNotExistedError` (400 Bad Request): Invalid judge name
- `CodeforcesContestNotFoundError` (404 Not Found): Contest not found (Codeforces-specific)

---

### Submission Management

#### UC-OJ-002: Submit

**Description:** Create a new submission.

**Actor:** Authenticated user

**Preconditions:**
- Exercise exists

**Main Flow:**
1. User provides exercise ID and verdict
2. System verifies exercise exists
3. System creates submission with generated submission ID
4. System stores submission
5. System returns Submission model

**Business Rules:**
- Submission ID generated as `invalid_{uuid}` for manual submissions
- Verdict is user-provided (for manual tracking)
- Links submission to both user and exercise

**Errors:**
- `ExerciseNotFoundError` (404 Not Found): Exercise does not exist

---

#### UC-OJ-003: Get Submissions

**Description:** Retrieve all submissions for a user on an exercise.

**Actor:** Authenticated user

**Preconditions:** None

**Main Flow:**
1. User provides user ID and exercise ID
2. System retrieves all submissions matching criteria
3. System returns list of Submission models

**Business Rules:**
- Returns empty list if no submissions found (not an error)
- Includes all submissions regardless of verdict
- Ordered by submission time (descending in repository)

**Errors:**
- `SubmissionNotFoundError` (404 Not Found): No submissions found

---

### User Judge Management

#### UC-OJ-004: Update User Judges

**Description:** Upsert user's external judge handles.

**Actor:** Authenticated user

**Preconditions:** None

**Main Flow:**
1. User provides list of (judge, handle) tuples
2. For each tuple, system creates or updates UserJudge record
3. System returns list of UserJudge models

**Business Rules:**
- Uses upsert semantics (insert or update)
- One handle per judge per user
- Previous handle replaced if updated

---

#### UC-OJ-005: Get User Judges

**Description:** Retrieve all judge handles for a user.

**Actor:** Authenticated user

**Preconditions:** None

**Main Flow:**
1. User provides user ID
2. System retrieves all UserJudge records for user
3. System returns list of UserJudge models

**Business Rules:**
- Returns empty list if no judges configured
- Includes `last_crawled` timestamp for each judge

---

### Crawling

#### UC-OJ-006: Crawl All Users

**Description:** Batch crawl submissions for all registered user judges.

**Actor:** System (scheduled task or admin)

**Preconditions:** None

**Main Flow:**
1. System retrieves all UserJudge entries
2. For each UserJudge:
   - Get appropriate judge instance from factory
   - Crawl submissions since `last_crawled` timestamp
   - For each submission:
     - Ensure exercise exists (create if needed)
     - Create submission record
   - Batch insert submissions (deduplication handled by repository)
   - Update `last_crawled` to latest submission timestamp
3. All changes committed atomically

**Business Rules:**
- Incremental crawling (only new submissions since last crawl)
- Timezone handling for `last_crawled` (assumes UTC if naive)
- Exercise auto-created if not in database
- Submission deduplication prevents duplicates
- `last_crawled` updated to track progress

---

## Error Reference

### LMS Errors

| Error | HTTP Status | Message | Trigger |
|-------|-------------|---------|---------|
| `UserExistedError` | 409 | User existed. | Registration with duplicate username |
| `UserNotFoundError` | 400 | Wrong credentials. | Login with unknown username |
| `UserWrongPasswordError` | 400 | Wrong credentials. | Login with wrong password |
| `NotAuthorizedError` | 401 | Not authorized. | Invalid or inactive session |
| `CourseNotFoundError` | 400 | Course not found. | Course ID does not exist |
| `CourseSlugExistsError` | 409 | Course slug already exists. | Duplicate course slug |
| `LessonSlugExistsError` | 409 | Lesson slug already exists in this course. | Duplicate lesson slug within course |
| `NotCourseAdminError` | 401 | Not a course admin. | Non-admin attempting admin action |
| `CannotRemoveLastAdminError` | 400 | Cannot remove the last admin. | Would leave course orphaned |

### OJ Errors

| Error | HTTP Status | Message | Trigger |
|-------|-------------|---------|---------|
| `JudgeNotExistedError` | 400 | Judge not existed | Invalid judge enum value |
| `ExerciseNotFoundError` | 404 | Exercise not found | Exercise ID does not exist |
| `SubmissionNotFoundError` | 404 | Submission not found | No submissions for query |
| `CodeforcesContestNotFoundError` | 404 | Codeforces contest not found | Invalid Codeforces contest ID |