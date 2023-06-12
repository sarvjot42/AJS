# using flask_restful

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS
import subprocess

# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)

CORS(app)

# making a class for a particular resource
# the get, post methods correspond to get and post requests
# they are automatically mapped by flask_restful.
# other methods include put, delete, etc.
class Hello(Resource):
    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource
    def get(self):
        return jsonify({'message': 'hello world'})

    # Corresponds to POST request
    def post(self):
        data = request.get_json()     # status code
        return jsonify({'data': data}), 201

# another resource to calculate the square of a number
class Square(Resource):
    def get(self, num):
        return jsonify({'square': num**2})

class Qst(Resource):
    def get(self):
        token = request.args.get('token')
        print_all = request.args.get('print_all')
        delay = request.args.get('delay')
        num_jstacks = request.args.get('num_jstacks')

        # Define the command to execute the Python script with command-line input
        script_path = "./qst2.py"
        command = ["python2", script_path, token]

        if print_all is not None and print_all != "null":
            command.append("-a")

        if delay is not None and delay != "null":
            command.append("-d")
            command.append(delay)

        if num_jstacks is not None and num_jstacks != "null":
            command.append("-n")
            command.append(num_jstacks)

        # Run the command and wait for it to complete
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode()  # Decode the bytes to string
        return jsonify({'output': stdout})

# adding the defined resources along with their corresponding urls
api.add_resource(Hello, '/')
api.add_resource(Square, '/square/<int:num>')
api.add_resource(Qst,'/qst')

# driver function
if __name__ == '__main__':
    app.run(debug = True)
