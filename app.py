from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "cupis-counter-python"


@app.route("/calculate-report", methods=['POST'])
async def load_cars():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    return 1
