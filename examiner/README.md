# EduExaminer – Online Examination (Quiz) System

> **Academic micro-project** for the course *Logic Building Using C* (First Semester).  
> Prototype only — see [Security & Limitations](#security--limitations) before any real deployment.

---

## Table of Contents
1. [Problem Statement & Objective](#problem-statement--objective)
2. [User Roles & Workflow](#user-roles--workflow)
3. [Implemented Features](#implemented-features)
4. [Technology Stack](#technology-stack)
5. [Architecture Overview](#architecture-overview)
6. [Data Flow](#data-flow)
7. [How to Run](#how-to-run)
8. [Demo Credentials](#demo-credentials)
9. [Course Outcome Mapping (CO1–CO4)](#course-outcome-mapping-co1co4)
10. [C Concepts Mapping](#c-concepts-mapping)
11. [Manual Test Table](#manual-test-table)
12. [Viva Preparation](#viva-preparation)
13. [Security & Limitations](#security--limitations)

---

## Problem Statement & Objective

Traditional paper-based MCQ examinations are time-consuming to administer, prone to manual errors during marking, and difficult to randomize. 

**EduExaminer** solves these problems by providing:
- A web-based platform where teachers can create and manage question banks, configure timed MCQ exams, and review student results.
- A student-facing portal where students can sign in, take assigned exams within a configured time window, and view their scores and history.

**Objective:** Demonstrate how core programming concepts — loops, arrays/collections, functions, and algorithms — are applied to build a real, working software product.

---

## User Roles & Workflow

```
Landing Page
│
├── Student Sign-In (email + password + register number)
│       │
│       └── Exam Menu → Confirm → Question-by-Question → Result → History
│
└── Teacher Sign-In (email + password)
        │
        └── Dashboard → Question Bank (CRUD) → Exam Config → Publish → View Attempts
```

### Teacher
1. Sign in with email and password.
2. Add/edit/delete MCQ questions (each with a subject, question text, variable number of options, and one correct answer).
3. Create an exam: choose subject, question count, shuffle on/off, duration, start/end window.
4. Publish the exam so students can access it.
5. View student attempts and scores from the exam detail page.

### Student
1. Sign in with email, password, and register number.
2. View available exams on the Examination Menu (open, upcoming, closed all shown).
3. Confirm before starting — a live clock and exam details are shown.
4. Answer one question at a time; Continue is locked until an answer is chosen.
5. Submit or auto-submit when the countdown timer expires.
6. See the Examination Finished page with score, correct/wrong/unanswered breakdown, and elapsed time.
7. View all past attempts on the History page.

---

## Implemented Features

| Feature | Status |
|---------|--------|
| Teacher login / logout | ✅ |
| Student login (email + password + register number) | ✅ |
| Question CRUD (create, read, update, delete) | ✅ |
| Variable option count per question (min 2) | ✅ |
| Question search & filter by subject | ✅ |
| Subject management (auto-created with questions) | ✅ |
| Exam configuration (duration, window, shuffle, count) | ✅ |
| Exam status lifecycle: Draft → Published → Closed | ✅ |
| Exam availability window enforcement (server-side) | ✅ |
| Confirmation dialog with live HH:MM:SS clock | ✅ |
| One-question-at-a-time exam flow | ✅ |
| Question shuffle (configurable) | ✅ |
| Countdown timer (persists across page refresh) | ✅ |
| Auto-submit on timer expiry | ✅ |
| Idempotent finish (double-submit safe) | ✅ |
| Score calculation with correct/wrong/unanswered breakdown | ✅ |
| Examination Finished page ("Well Done") | ✅ |
| Student attempt history | ✅ |
| Teacher attempt overview per exam | ✅ |
| Seed demo data command | ✅ |
| Responsive design (mobile, tablet, desktop) | ✅ |
| Keyboard-accessible, ARIA-labelled UI | ✅ |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Django 6.1 (Python) |
| Database | SQLite 3 (`db.sqlite3`) |
| Templating | Django Templates (Jinja-compatible syntax) |
| Styling | Custom CSS (design system in `static/examiner/css/examiner.css`) |
| JavaScript | Vanilla JS (`static/examiner/js/examiner.js`) — no frameworks |
| Password hashing | Django PBKDF2 (`make_password` / `check_password`) |
| Session management | Django server-side sessions |
| Fonts | Inter (Google Fonts CDN) |

---

## Architecture Overview

```
Browser
  │  HTTP requests (GET / POST)
  ▼
Django URL Router  (examiner/urls.py)
  │  routes to named view functions
  ▼
Views  (examiner/views.py)
  │  calls service functions only — no direct ORM
  ▼
Services  (examiner/services.py)
  │  all data operations, CO4 named functions
  ▼
Models  (examiner/models.py)
  │  ExamUser · Subject · Question · ExamConfig · Attempt
  ▼
SQLite Database  (db.sqlite3)
```

**Key design rule:** Views never query the database directly. All ORM calls are inside `services.py`. This keeps view code small and service functions testable in isolation.

---

## Data Flow

### Adding a Question
```
Teacher fills form → POST /teacher/questions/add/
  → question_add() view
    → add_question() service
      → validates (non-empty text, ≥2 options, correct option in options)
      → Question.objects.create(...)
      → redirect to question list
```

### Starting an Exam Attempt
```
Student clicks Start → POST /student/exam/<id>/confirm/
  → exam_confirm() view
    → start_attempt() service
      → checks exam.is_open()          [CO4: function]
      → select_questions_for_attempt() [CO3: slice + optional shuffle]
      → Attempt.objects.create(question_order=[...])
  → redirect to exam_question(attempt_id, index=0)
```

### Evaluating a Finished Attempt
```
Student finishes → GET /student/exam/<id>/finish/
  → exam_finish() view
    → finish_attempt() service
      → complete_attempt()
        → evaluate_attempt()           [CO4 + CO2: loop through question_order]
          → for pk in order:           [CO2: loop]
              answer = selected_answers[str(pk)]   [CO3: dict lookup]
              if answer == question.correct_option: score += 1
        → Attempt.score = score; Attempt.status = "completed"
  → redirect to exam_result
```

---

## How to Run

```bash
# 1. Open a terminal in the project root
#    C:\Users\josep\OneDrive\Documents\Antigravity

# 2. Activate the virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 3. Apply database migrations
python manage.py migrate

# 4. Seed demo data (teachers, students, subjects, questions, one exam)
python manage.py seed_examiner

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Start the development server
python manage.py runserver

# 7. Open in your browser
#    http://127.0.0.1:8000/examiner/
```

---

## Demo Credentials

| Role | Email | Password | Register No. |
|------|-------|----------|--------------|
| Teacher | `teacher@edu.example` | `teach123` | — |
| Student 1 | `student1@edu.example` | `student123` | `REG2024001` |
| Student 2 | `student2@edu.example` | `student123` | `REG2024002` |

> **Prototype only.** Credentials are intentionally visible in source code for demonstration. Never use this authentication scheme in production.

---

## Course Outcome Mapping (CO1–CO4)

### CO1 — Algorithm / Pseudocode

**Algorithm 1: Teacher adds a question**
```
BEGIN AddQuestion
  INPUT subject, question_text, options[], correct_option
  IF question_text is empty THEN
    OUTPUT error "Question text cannot be empty"
    STOP
  END IF
  IF count(options) < 2 THEN
    OUTPUT error "At least two options required"
    STOP
  END IF
  IF correct_option NOT IN option_ids THEN
    OUTPUT error "Correct option must match an option ID"
    STOP
  END IF
  SAVE Question(subject, question_text, options, correct_option)
  OUTPUT "Question added successfully"
END AddQuestion
```

**Algorithm 2: Student starts an exam**
```
BEGIN StartAttempt(student, exam)
  IF exam.status ≠ PUBLISHED THEN  STOP  END IF
  IF current_time NOT IN [exam.start, exam.end] THEN  STOP  END IF
  IF active_attempt exists for (student, exam) THEN
    RETURN existing attempt   // resume
  END IF
  all_pks ← GET all question PKs from exam.subject
  IF exam.shuffle THEN
    SHUFFLE all_pks          // CO3: sort/shuffle operation
  END IF
  selected_pks ← TAKE first exam.num_questions from all_pks  // CO2: slice
  CREATE Attempt(student, exam, question_order=selected_pks)
  RETURN new attempt
END StartAttempt
```

**Algorithm 3: Evaluate a finished attempt**
```
BEGIN EvaluateAttempt(attempt)
  correct ← 0;  wrong ← 0;  unanswered ← 0
  FOR EACH pk IN attempt.question_order DO    // CO2: loop
    question ← FIND question WHERE id = pk   // CO3: search by ID
    answer   ← attempt.selected_answers[pk]  // CO3: array/dict lookup
    IF answer is empty THEN
      unanswered ← unanswered + 1
    ELSE IF answer = question.correct_option THEN
      correct ← correct + 1
    ELSE
      wrong ← wrong + 1
    END IF
  END FOR
  RETURN {correct, wrong, unanswered, score=correct}
END EvaluateAttempt
```

---

### CO2 — Looping Constructs

| Loop | Location | Purpose |
|------|----------|---------|
| `for pk in order` | `services.py → evaluate_attempt()` L398 | Iterates every question in the attempt to classify the answer |
| `for pk in order` | `models.py → Attempt.grade()` L313 | Loops through question order to compute score |
| `for exam in exams` | `services.py → get_all_published_exams()` L543 | Iterates published exams to annotate each with open/upcoming/closed |
| `for qd in cs_questions` | `services.py → seed_demo_data()` L573 | Loops through question data to seed the database |
| `{% for opt in question.options %}` | `exam_question.html` L51 | Renders each answer option as a radio button |
| `{% for att in attempts %}` | `student_history.html` L49 | Renders each past attempt as a table row |
| `{% for exam in exams %}` | `teacher_dashboard.html` L100 | Renders exam list in dashboard table |
| `setInterval(tick, 1000)` | `examiner.js → startCountdownTimer()` | Loops every second to decrement and display the countdown |

---

### CO3 — Arrays, Searching and Sorting

| Operation | Location | Detail |
|-----------|----------|--------|
| **Store options as array** | `models.py → Question.options` (JSONField) | Each question stores its options as `[{"id":"A","text":"…"}, …]` |
| **Store question order as array** | `models.py → Attempt.question_order` (JSONField) | Ordered list of question PKs for the attempt |
| **Store answers as associative array** | `models.py → Attempt.selected_answers` (JSONField) | Dict `{str(pk): "option_id"}` — O(1) key lookup |
| **Filter/search by subject** | `services.py → search_questions()` L147 | `Question.objects.filter(subject_id=…, question_text__icontains=query)` |
| **Select subset from bank** | `services.py → select_questions_for_attempt()` L315 | `all_pks[: exam.num_questions]` — array slicing |
| **Shuffle (sort operation)** | `services.py → select_questions_for_attempt()` L326 | `random.shuffle(all_pks)` when `exam.shuffle_questions` is True |
| **Search by stable ID** | `services.py → evaluate_attempt()` L414 | `questions_map = {str(q.pk): q …}` then `questions_map.get(str(pk))` |
| **Find maximum (best score)** | `services.py → get_best_attempt()` L501 | `max(attempts, key=lambda a: a.score or 0)` |
| **Filter open exams** | `services.py → get_open_exams_for_student()` L513 | `ExamConfig.objects.filter(start__lte=now, end__gte=now)` |

> **Honest note on sorting:** Questions are stored in creation order and retrieved in that order unless shuffle is enabled. No explicit ascending/descending sort of questions by name or difficulty is currently implemented — that would be a natural next feature.

---

### CO4 — Functions and Modular Design

All service functions live in `examiner/services.py`. Each is small, clearly named, and does one thing.

**Authentication functions**

| Function | Lines | Purpose |
|----------|-------|---------|
| `authenticate_teacher(email, password)` | 32–44 | Verify teacher credentials, return user or None |
| `authenticate_student(email, password, register_number)` | 47–64 | Verify student credentials (3-factor) |
| `get_session_user(session)` | 67–75 | Retrieve logged-in user from session |
| `login_user(session, user)` | 78–81 | Write user PK to session |
| `logout_user(session)` | 84–87 | Clear session keys |
| `require_teacher(session)` | 94–105 | Guard — returns (user, error) |
| `require_student(session)` | 108–115 | Guard — returns (user, error) |

**Question management functions**

| Function | Lines | Purpose |
|----------|-------|---------|
| `list_questions_for_subject(subject_id)` | 139–144 | CO3: Return all questions for a subject |
| `search_questions(subject_id, query)` | 147–155 | CO3: Filter questions by text search |
| `add_question(subject, text, options, correct, …)` | 158–195 | CO4: Create question with validation |
| `edit_question(question_id, …)` | 198–228 | CO4: Update existing question |
| `delete_question(question_id)` | 231–237 | CO4: Delete by PK |

**Exam flow functions**

| Function | Lines | Purpose |
|----------|-------|---------|
| `select_questions_for_attempt(exam)` | 315–331 | CO3: Slice and optionally shuffle bank |
| `start_attempt(student, exam)` | 334–368 | CO4: Begin attempt, enforce window, resume if exists |
| `record_answer(attempt_id, question_pk, option_id)` | 371–386 | CO4: Save one answer safely |
| `finish_attempt(attempt_id)` | 389–395 | CO4: Delegate to complete_attempt (idempotent) |
| `complete_attempt(attempt_id, status)` | 459–483 | CO4: Grade + close attempt atomically |
| `evaluate_attempt(attempt)` | 398–448 | CO4+CO2: Loop and score all answers |
| `calculate_score(attempt)` | 450–457 | CO4: Thin wrapper returning (score, total) |
| `get_student_attempts(student)` | 485–499 | CO4: History query |
| `get_best_attempt(student)` | 501–510 | CO4+CO3: max() search on scores |

> **On recursion:** No recursion is used in EduExaminer. The problems solved here (iterating a list, scoring answers, shuffling) are naturally solved with loops — recursion would add complexity without benefit. Recursion would be appropriate if the data were hierarchical (e.g., a tree of question categories), which is not the case.

---

## C Concepts Mapping

> **Important academic distinction:** EduExaminer is written in Python (Django). It is **not** a C program. The table below shows how the *same algorithms* would be expressed in C using its native constructs.

| Concept | Python/Django (this project) | Equivalent in C |
|---------|------------------------------|-----------------|
| Question collection | `Question.objects.filter(…)` → Python list | `struct Question questions[MAX_Q];` array of structs |
| Options per question | `question.options` → Python list of dicts | `struct Option options[MAX_OPT];` inside the Question struct |
| Storing answers | `selected_answers = {str(pk): "A"}` → dict | `char answers[MAX_Q];` or `int answers[MAX_Q];` indexed by question position |
| Iterating questions | `for pk in order:` | `for (int i = 0; i < total; i++) { … }` |
| Shuffling | `random.shuffle(all_pks)` | Fisher-Yates shuffle loop on an `int pks[MAX_Q]` array |
| Search by subject | `filter(subject_id=x)` | `for` loop comparing `q.subject_id == x` |
| Count correct answers | `if chosen == q.correct_option: score += 1` | `if (strcmp(answer, q.correct) == 0) score++;` |
| Modular functions | `def evaluate_attempt(attempt):` | `int evaluateAttempt(Attempt *a, Question *bank, int total)` |
| Session / login state | Django session dict | Global `int logged_in_student_id;` or struct pointer |

### Sample C pseudocode — EvaluateAttempt

```c
/* CO4: Named function; CO2: for-loop; CO3: array lookup */
int evaluateAttempt(char answers[], int questionOrder[],
                    Question bank[], int total) {
    int score = 0;
    /* CO2: loop through each question index */
    for (int i = 0; i < total; i++) {
        int qIndex = questionOrder[i];         /* CO3: array lookup */
        char *correct = bank[qIndex].correct;  /* CO3: struct field access */
        /* CO3: search — compare answer string */
        if (strlen(answers[i]) > 0 &&
            strcmp(answers[i], correct) == 0) {
            score++;
        }
    }
    return score;
}
```

> If your instructor requires an actual runnable C submission, a separate `eduexaminer_console.c` file with a menu-driven console MCQ quiz can be prepared. The algorithms above translate directly.

---

## Manual Test Table

| # | Scenario | Expected Result | Observed Result |
|---|----------|-----------------|-----------------|
| 1 | Teacher signs in with correct credentials | Redirected to teacher dashboard | _(fill after running)_ |
| 2 | Teacher signs in with wrong password | Error "Invalid email or password." shown | _(fill after running)_ |
| 3 | Add question with 1 option | Error "at least two options" | _(fill after running)_ |
| 4 | Add question — correct_option not in options | Error "correct_option must match…" | _(fill after running)_ |
| 5 | Add valid question with 5 options | Question saved, appears in list | _(fill after running)_ |
| 6 | Edit question → save | Same question updated, not duplicated | _(fill after running)_ |
| 7 | Delete question → confirm | Question removed from bank | _(fill after running)_ |
| 8 | Search question bank | Only matching questions shown | _(fill after running)_ |
| 9 | Create exam with num_questions > bank size | Error shown, exam not created | _(fill after running)_ |
| 10 | Create valid exam → Publish | Exam status = Published | _(fill after running)_ |
| 11 | Student sign-in with wrong register number | Error "Invalid credentials" | _(fill after running)_ |
| 12 | Student sign-in with correct credentials | Redirected to Exam Menu | _(fill after running)_ |
| 13 | Open exam → Start | Confirmation dialog with live clock | _(fill after running)_ |
| 14 | Upcoming exam → Start button | Button disabled, shows "Opens …" | _(fill after running)_ |
| 15 | Closed exam → Start button | Button disabled, shows "Window closed" | _(fill after running)_ |
| 16 | Confirm dialog → Go Back | Returned to student sign-in | _(fill after running)_ |
| 17 | Confirm → Continue (no answer selected) | Continue button still disabled | _(fill after running)_ |
| 18 | Select answer → Continue | Next question shown, progress bar advances | _(fill after running)_ |
| 19 | Refresh exam question page | Countdown not reset; answer retained | _(fill after running)_ |
| 20 | Last question → Finish Exam | Result page shown | _(fill after running)_ |
| 21 | Result page: all correct | Score = total; 0 wrong; 0 unanswered | _(fill after running)_ |
| 22 | Result page: all wrong | Score = 0; wrong = total | _(fill after running)_ |
| 23 | Result page: mixed | Score correct; counts sum to total | _(fill after running)_ |
| 24 | Refresh result page | Score unchanged | _(fill after running)_ |
| 25 | Back-button to question after finish | Redirected to result page | _(fill after running)_ |
| 26 | Log Out from result | Redirected to landing page | _(fill after running)_ |
| 27 | My History page | All completed attempts listed | _(fill after running)_ |

---

## Viva Preparation

**Q: Why are loops used in EduExaminer?**  
Loops allow the program to process a *collection* of items without writing separate code for each one. For example, `evaluate_attempt()` uses a `for` loop to check every question in the attempt — if there are 10 questions, the same loop body runs 10 times. Without loops we would need 10 separate `if` blocks, making the code unscalable.

**Q: Why are arrays/collections used?**  
An exam has multiple questions, and each question has multiple options. Using an array (or Python list/dict) lets us store all items together and access any one by index or key. In C, `char answers[MAX_Q]` holds all student answers compactly; in Python, `selected_answers = {"12": "B", "15": "C"}` maps question IDs to chosen options in O(1) time.

**Q: How does searching by subject work?**  
`search_questions(subject_id, query)` filters the question database in two steps:  
1. **Filter by subject** — only keep questions whose `subject_id` matches.  
2. **Filter by text** — if a search query is given, further restrict to questions whose text contains the query (case-insensitive).  
This is equivalent to a linear search through an array in C: iterate all questions, include one only if `q.subject_id == target_subject && strstr(q.text, query) != NULL`.

**Q: Why do functions improve modularity?**  
Each function does one thing and has a clear name (`add_question`, `evaluate_attempt`, `get_student_attempts`). This means:  
- **Easier to read** — you understand what a function does from its name.  
- **Easier to test** — you can test `evaluate_attempt` with known answers without running the full web server.  
- **Easier to change** — fixing a bug in scoring only requires changing `evaluate_attempt`, not hunting through view code.

**Q: How does question shuffling work?**  
When a teacher enables shuffle, `select_questions_for_attempt()` runs `random.shuffle(all_pks)` on the list of question PKs before slicing. In C, this is a **Fisher-Yates shuffle**: iterate the array from the last index to 1; at each step, pick a random index ≤ current, and swap those two elements. The resulting order is stored in `Attempt.question_order` once at the start and never changed — so every refresh shows the same order.

**Q: How is the score calculated?**  
`evaluate_attempt(attempt)` loops through `attempt.question_order` (a list of question PKs). For each PK it:  
1. Looks up the student's answer in `attempt.selected_answers[str(pk)]`.  
2. Looks up the correct answer from the `Question` model.  
3. If they match, increments `correct`; if the answer is blank, increments `unanswered`; otherwise increments `wrong`.  
Final score = `correct`. Unanswered questions are **not** counted as correct.

---

## Security & Limitations

> [!WARNING]
> This is a **prototype** built for academic demonstration. It must not be used for real examinations without the following changes.

| Limitation | Required for Production |
|-----------|------------------------|
| `ExamUser` model is separate from Django's built-in auth | Use `django.contrib.auth.User`; add rate limiting and account lockout |
| Passwords hashed with PBKDF2 but no MFA | Add multi-factor authentication |
| Exam window enforced server-side per request | Also validate remaining time on every answer POST to prevent race conditions |
| Countdown timer persisted in browser `sessionStorage` | Server should compute and return remaining seconds on every question load |
| No HTTPS | Enforce `SECURE_SSL_REDIRECT = True` and HSTS |
| SQLite — single-file, no concurrent writes | Use PostgreSQL or MySQL in production |
| Correct answers stored server-side, never sent to browser | ✅ Already correct — maintain this |
| No audit log | Log every answer submission with timestamp for exam integrity |

---

*EduExaminer — micro-project documentation — 2026*

