from flask import Flask, request, render_template_string, render_template,redirect,flash
import pandas as pd
import urllib3
from forms import LoginForm
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
import time
from bs4 import BeautifulSoup

SECRET_KEY = os.urandom(32)

urllib3.disable_warnings()

pd.set_option('display.max_rows', 550)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', 70)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
menu = ['something', 'about']


@app.route('/', methods=['post', 'get'])
def start_form():
    form = LoginForm()
    return render_template('login.html', title='Sign In', form=form, menu=menu)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/index')
def index():
    return render_template('flask_app.html')


@app.route('/pars_yand')
def pars_yand():
    print('Yandex')
    url = 'https://ya.ru/'
    driver = webdriver.Chrome()
    driver.implicitly_wait(12)
    driver.get(url)
    time.sleep(5)
    driver.find_element(By.ID, "text").send_keys(f"{request.args.get('username')}\n")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    links = soup.findAll('div', {'class': 'Path Organic-Path path organic__path'})
    df = pd.DataFrame(columns=['Описание', 'Ссылка'])
    for link in links:
        if str(link.find().get('href')).startswith('https://yabs.yandex.ru/'):
            pass
        else:
            df_row = pd.DataFrame({'Описание': [request.args.get('username')], 'Ссылка': [f'{link.find().get("href")}']})
            df = pd.concat([df, df_row])

    print(df)

    return df.to_html(render_links=True, escape=False)

    # return request.args.get('username')

@app.route('/pars_goog')
def pars_goog():
    print('Google')
    return request.args.get('username')

if __name__ == '__main__':
    # app.run(debug=True)
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)