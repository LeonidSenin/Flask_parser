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
import sys
import numpy as np

import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama

SECRET_KEY = os.urandom(32)
urllib3.disable_warnings()

pd.set_option('display.max_rows', 550)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', 70)

app = Flask(__name__)
# CSRF_ENABLED = True
app.config['SECRET_KEY'] = SECRET_KEY

# инициализация наборов для ссылок (обеспечивается уникальность ссылок)
'''internal_urls — URL-адреса, которые ведут на другие страницы того же веб-сайта.
external_urls — URL-адреса, которые ведут на другие веб-сайты.'''
internal_urls = set()
external_urls = set()
total_urls_visited = 0


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
    class ReturnValueThread(Thread):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.result = None
        def run(self):
            if self._target is None:
                return  # could alternatively raise an exception, depends on the use case
            try:
                self.result = self._target(*self._args, **self._kwargs)
            except Exception as exc:
                print(f'{type(exc).__name__}: {exc}', file=sys.stderr)

        def join(self, *args, **kwargs):
            super().join(*args, **kwargs)
            return self.result

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

    def pars_yand():
        print('Yandex')
        url = 'https://ya.ru/'
        driver = webdriver.Chrome()
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

    df = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник', 'Дата'])

    # Параллельный запуск двух функций
    # -------------------------------------
    # thread1 = ReturnValueThread(target=pars_yand)
    # thread2 = ReturnValueThread(target=pars_goog)
    # thread1.start()
    # thread2.start()
    # thread1.join()
    # thread2.join()
    df = pd.concat([df, pars_goog()])

    #--------------------------------------------------
    # инициализация модуля colorama
    colorama.init()
    GREEN = colorama.Fore.GREEN
    GRAY = colorama.Fore.LIGHTBLACK_EX
    RESET = colorama.Fore.RESET
    YELLOW = colorama.Fore.YELLOW

    def is_valid(url):
        """
        Проверяет, является ли 'url' действительным URL
        """
        parsed = urlparse(url)
        # print(parsed)
        # print(bool(parsed.netloc) and bool(parsed.scheme))
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_all_website_links(url):
        """
        Возвращает все URL-адреса, найденные на `url`, в котором он принадлежит тому же веб-сайту.
        параметры: count_itteration (int): число задаваемых иттераций.
        """
        internal_urls = set()
        external_urls = set()

        # все URL-адреса `url`
        urls = set()
        external_urls_test = set()

        # доменное имя URL без протокола
        domain_name = urlparse(url).netloc
        soup = BeautifulSoup(requests.get(url, verify=False).content, "html.parser")

        # site = requests.get("https://rosstat.gov.ru/investment_nonfinancial", verify=False)
        # soup = BeautifulSoup(site.content, "html")

        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            # print(href)
            if href == "" or href is None:
                # href пустой тег
                continue
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # удалить GET-параметры URL, фрагменты URL и т. д.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid(href):
                # недействительный URL
                continue
            if href in internal_urls:
                # уже в наборе
                continue
            if domain_name not in href:
                # внешняя ссылка
                if href not in external_urls:
                    print(f"{GRAY}[!] Внешняя ссылка: {href}{RESET}")
                    external_urls.add(f"{href}")
                    external_urls_test.add(f"{href}")
                continue
            print(f"{GREEN}[*] Внутренняя ссылка: {href}{RESET}")
            urls.add(f"{href}")
            internal_urls.add(href)
        print(external_urls_test)

        # if len(external_urls_test) == 0 :
        #     print('heeere weeeeeee gooooooo!!!!!')
        #     external_urls_test.add('https://www.google.com/')

        return urls, external_urls_test

    def crawl(url):
        """
        Сканирует веб-страницу и извлекает все ссылки.
        Вы найдете все ссылки в глобальных переменных набора external_urls и internal_urls.
        """
        global total_urls_visited
        total_urls_visited += 1
        # print(f"{YELLOW}[*] Проверена ссылка: {url}{RESET}")
        try:
            internal_links, external_links = get_all_website_links(url)
            return external_links
        except:
            return [np.nan]

    def group_dataframe(list_of_first_itter):
        df_start = pd.DataFrame(list_of_first_itter, columns=['itteration_0'])
        count = 1
        n_count = 2
        while count <= n_count:
            # lst_new = []
            df_conc = pd.DataFrame()
            for i, row in df_start.iterrows():
                df = pd.DataFrame()
                df[f'itteration_{count}'] = list(crawl(row[f'itteration_{count - 1}']))
                df[f'itteration_{count - 1}'] = row[f'itteration_{count - 1}']
                df_conc = pd.concat([df_conc, df])
                # print(df_conc.info())
            try:
                df_start = pd.merge(df_start, df_conc, on=f'itteration_{count - 1}', how='inner')
            except:
                pass

            # print(df_start)
            # print(df_start.info())
            count += 1
        return df_start


    list_of_first_itter = list(set(df['Ссылка']))
    print(list_of_first_itter)
    # df_start = group_dataframe(list_of_first_itter)

    df_result = pd.DataFrame()
    for i in list_of_first_itter:
        lis = list()
        lis.append(i)
        df_start = group_dataframe(lis)
        df_result = pd.concat([df_result, df_start])
        # print(df_start)
    print(df_result)


    print("[+] Итого внутренних ссылок:", len(internal_urls))
    print("[+] Итого внешних ссылок:", len(external_urls))
    print("[+] Итого URL:", len(external_urls) + len(internal_urls))
    # print(df_start)
    # print(df_start.loc[(df_start['itteration_2'] == 'tel://+78007779075')])
    # -------------------------------------
    # df = pd.concat([df, pars_goog()])  # pars_yand()
    # df = pd.concat([df, pars_yand()])
    df_result.to_pickle('table.pkl')
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
    # http://localhost:8080/
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
