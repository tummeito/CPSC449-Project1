import os
from flask import Flask, request, jsonify, abort, redirect, url_for
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'project1_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
jwt = JWTManager(app)


@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad Request', 'message': 'Request form could not be recognized'}), 400

@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({'error': 'Unauthorized', 'message': 'You are not authorized to access this resource'}), 401

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found', 'message': 'Requested resources could not be located.'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong with the server'}), 500


users = [
    {"username": "admmin", "password": "password"}, 
    {"username": "user1", "password": "password1"}, 
    {"username": "user2", "password": "password2"}]

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splittext(filename)
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        upload_files.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    data=request.get_json()
    username = data['username']
    password = data['password']

    user = next((user for user in users if users['username'] == username), None)

    if user and user['password'] == password:
        access_token = create_access_token(identity=user)
        return jsonify(access_token=access_token), 200
    return jsonify(message="Invalid username or password"), 401

# Create new user endpoint
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if 'username' in data and 'password' in data:
        new_user = {
            "username": data['username'],
            "password": data['password']
        }
        users.append(new_user)
        return jsonify(new_user), 201
    return "Invalid POST request data", 400

# Read all users endpoint
@app.route('/users', methods=['GET'])
def get_items():
    return jsonify(users)

# Update a user endpoint
@app.route('/users/<string:user_username>', methods=['PUT'])
def update_user(user_username):
    data = request.get_json()
    user = next((user for user in users if users['username'] == user_username), None)
 
    if user is not None and 'username' in data: 
        user['username'] = data['username']
        return jsonify(user), 200
    return "User not found", 404

# Delete a user endpoint
@app.route('/users/<str:user_username>', methods=['DELETE'])
def delete_user(user_username):
    user = next((user for user in users if user['username'] == user_username), None)
    if user is not None:
        users.remove(user)
        return "User deleted", 204
    return "User not found", 404


# def hello_world():
#     return "hello world"


if __name__ == '__main__':
    app.run(debug=True)