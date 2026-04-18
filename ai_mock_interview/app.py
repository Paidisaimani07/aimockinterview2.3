from flask import Flask, render_template  # pyright: ignore[reportMissingImports]
from routes.interview_routes import interview_bp
#from ai_mock_interview.app import app
app = Flask(__name__)
app.register_blueprint(interview_bp)

@app.route("/")
def home():
    return render_template("interview.html")

@app.route("/result")
def result():
    return render_template("result.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)