from flask import Flask

app = Flask(__name__)

app.secret_key = "your-secret-key"

from routes.main import main
app.register_blueprint(main)


if __name__ == "__main__":
    app.run(debug=True)