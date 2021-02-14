import datetime
import json
import os

from flask import Flask, redirect, render_template, request, url_for
from flask_frozen import Freezer

from configuration import configuration

app = Flask(__name__);
freezer = Freezer(app)

@app.route("/")
def index():
    with open("data/data.json", "r", encoding="utf-8") as file_data:
        data = json.load(file_data);

    return render_template("index.html", data=data);

freezer.freeze()
