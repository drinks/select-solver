import os
import re
import json

from solver import choose, rank
from flask import Flask
app = Flask(__name__)
app.config.DEBUG = True if os.environ.get('DEBUG', False) == 'True' else False


@app.route('/choose.json')
def choose_endpoint():
    text = request.args.get('text', '')
    choices = request.args.get('choces', '')
    choices = re.split(r', ?', choices)
    return (json.dumps(choose(text, from_list=choices)), )


@app.route('/rank.json')
def rank_endpoint():
    text = request.args.get('text', '')
    choices = request.args.get('choces', '')
    choices = re.split(r', ?', choices)
    return (json.dumps(rank(text, from_list=choices)), )


if __name__ == '__main__':
    app.run()
