import flask

app = flask.Flask(__name__)

SAMPLE_QUESTIONS = (
    'What is your name?',
    'What is your favorite food?',
    'Do you have a nickname? If so, what is it?',
)

@app.route('/')
def quiz():
    return flask.render_template('main.html', id_and_questions=enumerate(SAMPLE_QUESTIONS))

if __name__ == '__main__':
    app.run(debug=True)
