import sqlite3

import flask

app = flask.Flask(__name__)

SAMPLE_QUESTIONS = (
    'What is your name?',
    'What is your favorite food?',
    'Do you have a nickname? If so, what is it?',
)

# Create an in-memory SQLite DB with toy data, just for now.
CONNECTION = sqlite3.connect(':memory:')

with CONNECTION:
    cursor = CONNECTION.cursor()

    # Create some tables.
    cursor.execute('''CREATE TABLE questions (
        id          INTEGER PRIMARY KEY,
        question    TEXT
    )''')

    cursor.execute('''CREATE TABLE answers (
        question_id                 INTEGER NOT NULL,
        user_id                     INTEGER PRIMARY KEY,
        answer                      TEXT,
        FOREIGN KEY(question_id)    REFERENCES questions(id)
    )''')

    # Add sample questions to the DB.
    # Generator expression looks funky, since each question needs to be a 1-tuple.
    cursor.executemany("INSERT INTO questions(question) VALUES (?)", ((q,) for q in SAMPLE_QUESTIONS))

@app.route('/')
def quiz():
    return flask.render_template('main.html', id_and_questions=enumerate(SAMPLE_QUESTIONS))

@app.route('/submit', methods=['POST'])
def on_submit():
    return f'<h1>Answers Submitted</h1>{flask.request.form}'

if __name__ == '__main__':
    app.run(debug=True)
