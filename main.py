import sqlite3
import pathlib as pl

import flask

app = flask.Flask(__name__)

SAMPLE_QUESTIONS = (
    'What is your name?',
    'What is your favorite food?',
    'Do you have a nickname? If so, what is it?',
)

USER_ID = 27

# Create a simple SQLite DB with toy data, just for now.
SQLITE_DB_PATH = pl.Path('store.db')

with sqlite3.connect(SQLITE_DB_PATH) as conn:
    cursor = conn.cursor()

    # Delete tables if they already exist.
    cursor.execute('DROP TABLE IF EXISTS questions')
    cursor.execute('DROP TABLE IF EXISTS answers')

    # Create some tables.
    cursor.execute('''CREATE TABLE questions (
        id          INTEGER PRIMARY KEY,
        question    TEXT
    )''')

    cursor.execute('''CREATE TABLE answers (
        question_id                 INTEGER NOT NULL,
        user_id                     INTEGER NOT NULL,
        answer                      TEXT,
        FOREIGN KEY(question_id)    REFERENCES questions(id),
        PRIMARY KEY(question_id, user_id)
    )''')

    # Add sample questions to the DB.
    # Generator expression looks funky, since each question needs to be a 1-tuple.
    cursor.executemany("INSERT INTO questions(question) VALUES (?)", ((q,) for q in SAMPLE_QUESTIONS))

@app.route('/')
def quiz():
    # Load the sample questions and ids from the database.
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()

        ids_and_questions = cursor.execute('SELECT id, question FROM questions ORDER BY id')

        return flask.render_template('main.html', id_and_questions=ids_and_questions)

@app.route('/submit', methods=['POST'])
def on_submit():
    ids_and_answers = ((int(q_id), answer) for q_id, answer in flask.request.form.items())

    conn = sqlite3.connect(SQLITE_DB_PATH)

    # Save answers into DB.
    with conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO answers(question_id, answer, user_id) VALUES (?, ?, ?)',
            ((i, a, USER_ID) for i, a in ids_and_answers),
        )

    # Read the saved answers back out.
    with conn:
        cursor = conn.cursor()
        q_and_a = cursor.execute('''SELECT q.question, a.answer
            FROM questions AS q, answers AS a
            WHERE q.id = a.question_id'''
        )
        return flask.render_template('submit.html', questions_and_answers=q_and_a)

@app.route('/submit_q/<int:q_id>', methods=['POST'])
def on_submit_q(q_id):
    conn = sqlite3.connect(SQLITE_DB_PATH)

    # Save the result of the just-answered question.
    ids_and_answers = ((int(q_id), answer) for q_id, answer in flask.request.form.items())
    with conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO answers(question_id, answer, user_id) VALUES (?, ?, ?)',
            ((i, a, USER_ID) for i, a in ids_and_answers),
        )

    # Load the next question, or redirect to the final landing page.
    with conn:
        next_q_id = conn.execute(f'SELECT id FROM questions ORDER BY id LIMIT 1 WHERE id > {q_id}')

        if next_q_id is None:
            # Done, redirect to the final landing page.
        else:
            # More to go, redirect to the next page.

if __name__ == '__main__':
    app.run(debug=True)
