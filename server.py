from helper import MigrosAPI
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
mgrs = MigrosAPI()


app = Flask(__name__, static_url_path='',
            static_folder='build',
            template_folder='build')

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/risks_for_order")
def get_risks_for_order():
    order_id = request.args.get('order_id')
    return jsonify(mgrs.get_risks_for_order_id(order_id))


@app.route("/risks_for_ports")
def get_risks_for_ports():
    return jsonify(mgrs.get_risks_for_ports())


app.run(debug=True, host='0.0.0.0', port=5000)
