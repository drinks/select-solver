import os
import re
import json

from solver import choose, rank
from flask import Flask, request
app = Flask(__name__)
app.config['DEBUG'] = True if os.environ.get('DEBUG', False) == 'True' else False


def parse_input():
    text = request.args.get('text')
    choices = request.args.get('choices', '')
    choices = re.split(r', ?', choices)
    return (text, choices)


@app.route('/choose.json')
def choose_endpoint():
    (text, choices) = parse_input()
    return json.dumps(choose(text, from_list=choices)), 200


@app.route('/rank.json')
def rank_endpoint():
    (text, choices) = parse_input()
    return json.dumps(rank(text, from_list=choices)), 200


if __name__ == '__main__':
    app.run()
