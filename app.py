from flask import Flask, render_template, request, jsonify
from feed_library import feeds

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', feeds=feeds)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')