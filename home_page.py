from flask import Flask, request, render_template, redirect
import pandas as pd
import urllib3
from forms import LoginForm ,TableFrom
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
import time
from bs4 import BeautifulSoup
import datetime

from threading import Thread
import pretty_html_table


SECRET_KEY = os.urandom(32)

urllib3.disable_warnings()

pd.set_option('display.max_rows', 550)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', 70)

app = Flask(__name__)
# CSRF_ENABLED = True
app.config['SECRET_KEY'] = SECRET_KEY


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

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")

@app.route('/pars')
def pars():
    name = request.args.get('username')
    period = datetime.datetime.now()
    def pars_goog():
        print('Google')
        url = 'https://www.google.com/'
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        driver.get(url)
        # time.sleep(5)
        driver.find_element(By.ID, "APjFqb").send_keys(f"{name}\n")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        df = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник'])
        for links in soup.findAll('div', {'class': 'MjjYud'}):
            for link in links:
                if link.find('a') != None:
                    if link.find('a').get('href').startswith('https'):
                        df_row = pd.DataFrame(
                            {'Описание': [name], 'Ссылка': [f'{link.find("a").get("href")}'], 'Источник': ['Google'],
                             'Дата': period})
                        df = pd.concat([df, df_row])
                else:
                    pass
        return df
        # return df.to_html(render_links=True, escape=False)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    def pars_yand():
        print('Yandex')
        url = 'https://ya.ru/'
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(12)
        driver.get(url)
        time.sleep(5)
        driver.find_element(By.ID, "text").send_keys(f"{name}\n")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        links = soup.findAll('div', {'class': 'Path Organic-Path path organic__path'})
        df = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник'])
        for link in links:
            if str(link.find().get('href')).startswith('https://yabs.yandex.ru/'):
                pass
            else:
                df_row = pd.DataFrame({'Описание': [name], 'Ссылка': [f'{link.find().get("href")}'], 'Источник': ['Yandex'], 'Дата': period})
                df = pd.concat([df, df_row])
        return df


    # Параллельный запуск двух функций (в доработке)
    # -------------------------------------
    # thread1 = Thread(target=pars_yand)
    # thread2 = Thread(target=pars_goog)
    # first = thread1.start()
    # second = thread2.start()
    # thread1.join()
    # thread2.join()
    # df = pd.concat([df, first, second])
    # -------------------------------------

    df = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник', 'Дата'])
    df = pd.concat([df, pars_goog()])  # pars_yand()
    df = pd.concat([df, pars_yand()])
    df.to_pickle('table.pkl')
    return redirect('/table')

@app.route('/table')
def dash_table():
    form = TableFrom()
    df = pd.read_pickle('table.pkl')
    # два варианта отрисовки
    # df.insert(loc=4, column='check_box', value=f"<input type='checkbox' checked=''>")
    # df.insert(loc=4, column='check_box', value=f"<select> <option value='apple'>Да</option> <option value='banana' selected >Нет</option></select>")
    table = df.to_html(render_links=True, index=False, classes='mystyle', escape=False)
    return render_template('table.html', title='Таблица', form=form, table=table)
    # return html_string.format(table=df.to_html(render_links=True, index=False, classes='mystyle', escape=False))


if __name__ == '__main__':
    # app.run(debug=True)
    # http: // localhost: 8080 /
    #http://localhost:8080/
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
