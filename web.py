import datetime
import json
import os
import shutil

from flask import Flask, render_template
from flask_frozen import Freezer

from configuration import configuration

app = Flask(__name__);
freezer = Freezer(app);

@app.route("/")
def index():
    with open("data/data.json", "r", encoding="utf-8") as file_data:
        data = json.load(file_data);

    return render_template("index.html", data=data);

freezer.freeze()
shutil.copyfile("build/index.html", "index.html");
