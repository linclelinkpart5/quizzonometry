import sqlite3
import pathlib as pl
import typing as tp

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


def next_question_row(curr_q_id: tp.Optional[int]) -> tp.Optional[tp.Tuple[int, str]]:
    '''Given an optional current question id (as would be in the DB),
    returns the next question id and text immediately after it, if it exists.
    If the current id is None, returns the first question id and text,
    if it exists.'''

    sql_lines = [
        'SELECT id, question',
        'FROM questions',
        'ORDER BY id',
        'LIMIT 1',
    ]

    # Add the where clause if we want to continue where we left off.
    if curr_q_id is not None:
        where_clause = f'WHERE id > {curr_q_id}'
        sql_lines.append(where_clause)

    sql = ' '.join(sql_lines)

    conn = sqlite3.connect(SQLITE_DB_PATH)

    # Save answers into DB.
    with conn:
        query = conn.execute(sql)
        return query.fetchone()


@app.route('/')
def quiz():
    # Load the first question and id from the database.
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


@app.route('/question/<int:q_id>')
def question(q_id):
    conn = sqlite3.connect(SQLITE_DB_PATH)

    # Save the result of the just-answered question.
    with conn:
        cursor = conn.cursor()
        query = cursor.execute(f'SELECT question FROM questions WHERE id = {q_id}')

        # We assume that the `q_id` is valid.
        # If it wasn't, we could either display an error, or gracefully redirect
        # to the finish page (which requires the same code in the submit logic).
        q = query.fetchone()[0]

        # This should figure out the actual N, since the N-th question may
        # not have an id lining up with N. But doing a simple approach for now.
        return flask.render_template('question.html', n=q_id, q_id=q_id, q=q)


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

    next_question_row = next_question_row(q_id)

    if next_question_row is None:
        # Done, redirect to final landing page.
        return flask.redirect(flask.url_for('finish'))

    # Otherwise, redirect to the next question.
    next_q_id, _ = next_question_row
    return flask.redirect(flask.url_for('question'), q_id=next_q_id)


@app.route('/finish')
def on_finish():
    conn = sqlite3.connect(SQLITE_DB_PATH)

    # Read the saved answers back out.
    with conn:
        cursor = conn.cursor()
        q_and_a = cursor.execute(f'''SELECT q.question, a.answer
            FROM questions AS q, answers AS a
            WHERE q.id = a.question_id AND a.user_id = {USER_ID}'''
        )
        return flask.render_template('finish.html', questions_and_answers=q_and_a)


if __name__ == '__main__':
    app.run(debug=True)
