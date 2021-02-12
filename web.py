import datetime
import json
import os

from flask import Flask, redirect, render_template, request, url_for

from configuration import configuration

app = Flask(__name__);

@app.route("/")
def index():
    with open("data/data.json", "r", encoding="utf-8") as file_data:
        data = json.load(file_data);

    return render_template("index.html", data=data);

app.run(debug=True);
