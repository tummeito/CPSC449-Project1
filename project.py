import os
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, abort
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
# from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
import jwt
from datetime import datetime, timedelta
from functools import wraps
import re
app = Flask(__name__)
# jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace with a secure secret key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # You can configure token expiration
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False  # or use timed expiration

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskproject'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/flaskproject"

app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'

mysql = MySQL(app)

#Setting up User Model
db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Default statement setting up database
@app.route('/')
def index():
    try:
        # Creating a connection cursor
        cursor = mysql.connection.cursor()

        # Executing SQL Statements
        cursor.execute(''' CREATE TABLE IF NOT EXISTS user_table (
                    user_id INT AUTO_INCREMENT PRIMARY KEY, 
                    username VARCHAR(80) UNIQUE NOT NULL, 
                    password VARCHAR(120) NOT NULL) ''')
        cursor.execute(''' INSERT IGNORE INTO user_table(username, password) VALUES ('admin', 'password') ''')
        cursor.execute(''' INSERT IGNORE INTO user_table(username, password) VALUES ('user1', 'password1') ''')
        cursor.execute(''' INSERT IGNORE INTO user_table(username, password) VALUES ('user2', 'password2') ''')

        # Saving the actions performed on the DB
        mysql.connection.commit()

        # Closing the cursor
        cursor.close()

        return "Database operations successful"

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Token authenticator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            # return jsonify({'token':token})
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
        except:
            return jsonify({
                'message' : 'Token is invalid !!',
                'token': token
            }), 401
        # returns the current logged in users context to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated

# Admin authenticator
def admmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        if current_user == "admin":        
            return  f(current_user, *args, **kwargs)
        else:
            return jsonify({
                'message' : 'No Authorization'
            }), 401
  
    return decorated

# Upload file endpoint
@app.route('/upload', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
        abort(400)
    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return jsonify({'msg': 'File uploaded'})

# Get all users endpoint
@app.route('/users', methods=['GET'])
def get_all_users():
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM user_table''')
    results = cursor.fetchall()
    output = []
    for user in results:
        output.append({
            'user_id': user['user_id'],
            'username': user['username'],
            'password': user['password']
        })
    cursor.close()
    return jsonify(output)

# Add new user to table endpoint
@app.route('/users', methods=['POST'])
def create_user():
    cursor = mysql.connection.cursor()
    try:
        new_username = request.json['username']
        new_password = request.json['password']
        cursor.execute(''' INSERT IGNORE INTO user_table(username, password) VALUES(%s, %s)''' , (new_username, new_password))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'New user added'})
    except:
        cursor.close()
        return jsonify({'error': 'Invalid operations'}), 401
    

# Get a user endpoint
@app.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM user_table WHERE username=%s ''', (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'User not found'})

# Update user endpoint
@app.route('/users/<string:username>', methods=['POST'])
def update_user(username):
    try:
        cursor = mysql.connection.cursor()
        new_username = request.json['username']
        new_password = request.json['password']
        cursor.execute(''' UPDATE user_table SET username=%s, password=%s WHERE username=%s''', (new_username, new_password, username,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'User updated!!'})
    except:
        cursor.close()
        return jsonify({'error': 'Invalid operations'}), 401
        

# Delete user from table endpoint
@app.route('/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(''' DELETE FROM user_table WHERE username=%s ''', (username,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'User deleted'})
    except:
        cursor.close()
        return jsonify({'error': 'Invalid operations'}), 401


@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if (request.method == 'POST' and 'username' in request.form and
       'password' in request.form):
       username = request.form['username']
       password = request.form['password']
       cursor = mysql.connection.cursor()
       cursor.execute('SELECT * FROM user_table WHERE username = %s AND password = %s', (username, password,))
       account = cursor.fetchone()

       if account:
           msg = 'Logged in successfully !'
           token = jwt.encode({
               'username': username,
               'exp': datetime.utcnow() + timedelta(minutes = 60)
           }, app.config['JWT_SECRET_KEY'])
           return jsonify({'token' : jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256']),
                           'encoded_token' : token}), 201
       else:
           msg = 'Incorrect username or password !'
    return jsonify({'message': msg})

@app.route('/protected')
@token_required
def protected(current_user):
    return("This is a protected endpoint that requires tokens")

@app.route('/protected/admin')
@admmin_required
def admin_protected(current_user):
    return("This a protected endpoint that requires admin token")


#@app.route('/')
#def index():
#    # Check if the client has a 'unique_id' cookie
#    unique_id = request.cookies.get('unique_id')
#    if unique_id:
#        return f"Welcome back! Your unique ID is: {unique_id}"
#        app.run()
#    else:
#        # Generate a new unique ID
#        new_unique_id = str(unique_id)
#        # Create a response and set a 'unique_id' cookie
#        response = make_response(f"Hello! Your unique ID is: {new_unique_id}")
#        response.set_cookie('unique_id', new_unique_id)
#        return response
#        if __name__ == '__main__':
#            import uuid
#            app.run()


# Error handler for HTTP 400 (Bad Request)
@app.errorhandler(400)
def bad_request(error):
    return jsonify(error='Error 400: Bad Request'), 400

# Error handler for HTTP 401 (Unauthorized)
@app.errorhandler(401)
def unauthorized(error):
    return jsonify(error='Error 401: Unauthorized'), 401

# Error handler for HTTP 404 (Not Found)
@app.errorhandler(404)
def not_found(error):
    return jsonify(error='Error 404: Not Found'), 404

# Error handler for HTTP 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify(error='Error 500: Internal Server Error'), 500

# Custom route to trigger errors for testing
@app.route('/trigger_error/<int:error_code>')
def trigger_error(error_code):
    if error_code == 400:
        return 'Triggering a 400 error', 400
    elif error_code == 401:
        return 'Triggering a 401 error', 401
    elif error_code == 404:
        return 'Triggering a 404 error', 404
    elif error_code == 500:
        raise Exception('Triggering a 500 error')
    else:
        return 'No error triggered'


if __name__ == '__main__':
    app.run(debug=True)