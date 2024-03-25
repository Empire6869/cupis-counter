from flask import Flask, request, jsonify
from reports import Reports
from flask import Response
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "cupis-counter-python"


@app.route("/calculate-report", methods=['POST'])
async def load_cars():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    [error, report] = Reports().get_report(username, password)

    if error == 'LoginPasswordError':
        return Response("LoginPasswordError", status=401)
    
    if error == 'TechAuthError':
        return Response("TechAuthError", status=403)
    
    if error == 'PasswordTooShort':
        return Response("TechAuthError", status=402)

    return jsonify(report)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)