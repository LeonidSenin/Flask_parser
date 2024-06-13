from flask import Flask, render_template, redirect, request
import pandas as pd
import urllib3
from forms import LoginForm
import os
from parser_page import app1_blueprint  # Импортируем Blueprint parser_page
from show_table import app2_blueprint  # Импортируем Blueprint из show_table

SECRET_KEY = os.urandom(32)
urllib3.disable_warnings()

pd.set_option('display.max_rows', 550)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', 70)

app = Flask(__name__)
# app.run(debug=True)
app.config['SECRET_KEY'] = SECRET_KEY
app.register_blueprint(app1_blueprint, url_prefix='/app1')
app.register_blueprint(app2_blueprint, url_prefix='/app2')

@app.route('/', methods=['post', 'get'])
def start_form():
    form = LoginForm()
    message = "После нажатия на кнопку 'Искать' подождите результата!"
    return render_template('login.html', title='Home page', form=form, message=message)

@app.route('/about')
def about():
    return render_template('about.html', title='About page')

@app.route('/index')
def index():
    return render_template('flask_app.html', title='Flask_app page')

@app.route('/pars')
def parsing_site():
    query_string = request.query_string.decode()
    return redirect(f'/app1/pars?{query_string}') # Перенаправление с сохранением параметров запроса

if __name__ == '__main__':
    # http://localhost:8080/
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)

