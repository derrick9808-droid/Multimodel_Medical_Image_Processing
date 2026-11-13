/*
 * EduExaminer — Console MCQ Quiz (C Pseudocode / Skeleton)
 * ==========================================================
 * This file shows how the SAME algorithms used in the Django web app
 * translate into C using arrays, structs, loops, and functions.
 *
 * Course Outcome Mapping:
 *   CO1 — Algorithm design (see comments before each function)
 *   CO2 — Looping constructs (for loops throughout)
 *   CO3 — Arrays, searching, shuffling (question bank, answers array)
 *   CO4 — Functions (each operation is a named, focused function)
 *
 * NOTE: This is a teaching aid / pseudocode skeleton.
 *       Complete I/O, error handling, and string safety would be needed
 *       for a fully runnable submission.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── Constants ─────────────────────────────────────────────────────── */
#define MAX_QUESTIONS   100
#define MAX_OPTIONS     10
#define MAX_STR         256
#define MAX_STUDENTS    50

/* ── Structures (CO3: array-of-structs, equivalent to Django models) ─ */

typedef struct {
    char id[8];         /* e.g. "A", "B", "C" */
    char text[MAX_STR];
} Option;

typedef struct {
    int     pk;
    char    subject[MAX_STR];
    char    question_text[MAX_STR];
    Option  options[MAX_OPTIONS];
    int     num_options;
    char    correct_option[8]; /* matches one Option.id */
} Question;

typedef struct {
    int  question_order[MAX_QUESTIONS]; /* CO3: array of question indexes */
    char answers[MAX_QUESTIONS][8];     /* CO3: answers[i] = chosen option id */
    int  total;
    int  score;
    int  correct;
    int  wrong;
    int  unanswered;
} Attempt;


/* ── CO3: Searching ─────────────────────────────────────────────────
   Algorithm: linear search through question array by subject.
   Equivalent to Django: Question.objects.filter(subject=subject)
   ──────────────────────────────────────────────────────────────────── */
int filterBySubject(Question bank[], int bankSize,
                    const char *subject,
                    int result[], int maxResults) {
    int count = 0;
    /* CO2: for-loop — iterate every question in the bank */
    for (int i = 0; i < bankSize && count < maxResults; i++) {
        if (strcmp(bank[i].subject, subject) == 0) { /* CO3: search */
            result[count++] = i;
        }
    }
    return count; /* number of matches */
}


/* ── CO3: Shuffling (Fisher-Yates algorithm) ────────────────────────
   Algorithm:
     FOR i FROM n-1 DOWN TO 1
       j ← random integer in [0, i]
       SWAP arr[i] and arr[j]
   END FOR
   Equivalent to Django: random.shuffle(all_pks)
   ──────────────────────────────────────────────────────────────────── */
void shuffleArray(int arr[], int n) {
    srand((unsigned int)time(NULL));
    /* CO2: for-loop counting down */
    for (int i = n - 1; i > 0; i--) {
        int j = rand() % (i + 1); /* CO3: random index in [0, i] */
        int tmp = arr[i];          /* swap */
        arr[i] = arr[j];
        arr[j] = tmp;
    }
}


/* ── CO4: selectQuestionsForAttempt ─────────────────────────────────
   CO1 Algorithm:
     GET all question indexes for the subject  (CO3: filter)
     IF shuffle THEN apply Fisher-Yates        (CO3: sort/shuffle)
     TAKE first numQuestions indexes           (CO3: slice)
   ──────────────────────────────────────────────────────────────────── */
int selectQuestionsForAttempt(Question bank[], int bankSize,
                               const char *subject,
                               int numQuestions, int shuffle,
                               int selected[]) {
    int pool[MAX_QUESTIONS];
    int poolSize = filterBySubject(bank, bankSize, subject,
                                   pool, MAX_QUESTIONS);

    if (shuffle) {
        shuffleArray(pool, poolSize);  /* CO3: shuffle */
    }

    int take = (numQuestions < poolSize) ? numQuestions : poolSize;
    /* CO2: loop to copy selected indexes */
    for (int i = 0; i < take; i++) {
        selected[i] = pool[i];
    }
    return take;
}


/* ── CO4: evaluateAttempt ───────────────────────────────────────────
   CO1 Algorithm:
     FOR EACH question in attempt.question_order  (CO2: loop)
       answer ← attempt.answers[i]               (CO3: array lookup)
       IF answer empty THEN unanswered++
       ELSE IF answer == bank[q].correct THEN correct++
       ELSE wrong++
     END FOR
     score = correct
   ──────────────────────────────────────────────────────────────────── */
void evaluateAttempt(Attempt *attempt, Question bank[]) {
    attempt->correct    = 0;
    attempt->wrong      = 0;
    attempt->unanswered = 0;

    /* CO2: for-loop over question order */
    for (int i = 0; i < attempt->total; i++) {
        int qIdx   = attempt->question_order[i];       /* CO3: array lookup */
        char *ans  = attempt->answers[i];              /* CO3: array lookup */
        char *corr = bank[qIdx].correct_option;        /* CO3: struct field */

        if (strlen(ans) == 0) {
            attempt->unanswered++;
        } else if (strcmp(ans, corr) == 0) {           /* CO3: search/compare */
            attempt->correct++;
        } else {
            attempt->wrong++;
        }
    }
    attempt->score = attempt->correct; /* unanswered ≠ correct */
}


/* ── CO4: displayQuestion ───────────────────────────────────────────
   Show one question with its options.
   CO2: for-loop to render each option.
   ──────────────────────────────────────────────────────────────────── */
void displayQuestion(Question *q, int number, int total) {
    printf("\n--- Question %d of %d ---\n", number, total);
    printf("%s\n\n", q->question_text);

    /* CO2: for-loop — iterate over options array */
    for (int i = 0; i < q->num_options; i++) {
        printf("  [%s] %s\n", q->options[i].id, q->options[i].text);
    }
    printf("\nYour answer: ");
}


/* ── CO4: conductExam ───────────────────────────────────────────────
   CO1 Algorithm:
     SELECT questions for attempt
     FOR EACH question (CO2: loop)
       DISPLAY question and options
       INPUT answer from student
       SAVE answer to answers[]
     END FOR
     EVALUATE attempt
     DISPLAY result
   ──────────────────────────────────────────────────────────────────── */
void conductExam(Question bank[], int bankSize,
                 const char *subject, int numQuestions, int shuffle) {
    Attempt attempt = {0};
    int selected[MAX_QUESTIONS];

    /* CO4: selectQuestionsForAttempt */
    attempt.total = selectQuestionsForAttempt(
        bank, bankSize, subject, numQuestions, shuffle, selected
    );

    /* Copy selected to question_order */
    for (int i = 0; i < attempt.total; i++) {
        attempt.question_order[i] = selected[i];
    }

    /* CO2: main exam loop — one question at a time */
    for (int i = 0; i < attempt.total; i++) {
        int qIdx = attempt.question_order[i];
        displayQuestion(&bank[qIdx], i + 1, attempt.total); /* CO4 */
        scanf("%7s", attempt.answers[i]);                   /* CO3: store in array */
    }

    /* CO4: evaluate */
    evaluateAttempt(&attempt, bank);

    /* CO4: display result */
    printf("\n========== Examination Finished ==========\n");
    printf("Well Done!\n\n");
    printf("Score      : %d / %d\n", attempt.score, attempt.total);
    printf("Correct    : %d\n", attempt.correct);
    printf("Wrong      : %d\n", attempt.wrong);
    printf("Unanswered : %d\n", attempt.unanswered);
    printf("==========================================\n");
}


/* ── CO4: main — entry point with simple menu ───────────────────────
   CO1 Algorithm:
     DISPLAY menu
     READ choice
     IF choice == 1 THEN conductExam(...)
     IF choice == 2 THEN EXIT
   ──────────────────────────────────────────────────────────────────── */
int main(void) {
    /*
     * Sample question bank (in production, load from file or database)
     * CO3: array of Question structs
     */
    Question bank[MAX_QUESTIONS] = {
        {
            1, "Computer Science",
            "Which data structure uses LIFO ordering?",
            {{"A","Queue"},{"B","Stack"},{"C","Linked List"},{"D","Binary Tree"}},
            4, "B"
        },
        {
            2, "Computer Science",
            "What is the time complexity of binary search?",
            {{"A","O(n)"},{"B","O(n^2)"},{"C","O(log n)"},{"D","O(1)"}},
            4, "C"
        },
        {
            3, "Computer Science",
            "Which sort has best average complexity?",
            {{"A","Bubble O(n^2)"},{"B","Selection O(n^2)"},
             {"C","Merge O(n log n)"},{"D","Insertion O(n^2)"}},
            4, "C"
        }
    };
    int bankSize = 3;

    int choice;
    printf("===== EduExaminer Console Quiz =====\n");
    printf("1. Start Exam\n");
    printf("2. Exit\n");
    printf("Choice: ");
    scanf("%d", &choice);

    if (choice == 1) {
        /* CO4: conductExam handles the full exam flow */
        conductExam(bank, bankSize, "Computer Science", 2, 1 /*shuffle=yes*/);
    }

    return 0;
}

/*
 * To compile and run (GCC):
 *   gcc -o eduexaminer eduexaminer_c_mapping.c
 *   ./eduexaminer
 *
 * On Windows (MinGW / MSYS2):
 *   gcc -o eduexaminer.exe eduexaminer_c_mapping.c
 *   eduexaminer.exe
 */

