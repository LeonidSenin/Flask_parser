from flask import request, redirect, Blueprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
import datetime
import numpy as np
import pandas as pd
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import re
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from tqdm import tqdm

from data_research_keywords import rake_nltk
load_dotenv()
constant = os.getenv

# Объявляем глобальные переменные
user = constant("db_user")
passw = constant("db_passw")
host = constant('db_host')
port = constant('db_port')

app1_blueprint = Blueprint('app1', __name__)

# инициализация наборов для ссылок (обеспечивается уникальность ссылок)
'''internal_urls — URL-адреса, которые ведут на другие страницы того же веб-сайта.
external_urls — URL-адреса, которые ведут на другие веб-сайты.'''
internal_urls = set()
external_urls = set()
total_urls_visited = 0

TABLE_NAME = 'pars_data'
SCHEMA_NAME = 'dataset'
engine = create_engine(f'postgresql://{user}:{passw}@{host}:{port}/ac_data')

# инициализация модуля colorama
colorama.init()
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")

def get_html_with_delay(url):
    """
        Получает HTML содержимое страницы с задержкой и парсит его с помощью BeautifulSoup.
        Возвращает текстовое содержимое страницы.
    """
    try:
        response = requests.get(url, verify=False,timeout=3)
        soup = BeautifulSoup(response.content, "html.parser")
        return get_html(soup)
    except:
        pass

def get_html(soup):
    """
        Извлекает и очищает текст из объекта BeautifulSoup.
    """
    try:
        text = soup.get_text()
        text = re.sub(r'\<[^>]*\>', '', text)
        # text = bleach.clean(html, tags=[], strip=True)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\t', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    except:
        pass

def is_valid(url):
    """
    Проверяет, является ли 'url' действительным URL
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url):
    """
    Возвращает все URL-адреса, найденные на `url`, которые принадлежат тому же веб-сайту.
    """

    # все URL-адреса `url`
    urls = set()
    external_urls_test = []
    page_text = []

    # доменное имя URL без протокола
    domain_name = urlparse(url).netloc

    soup = BeautifulSoup(requests.get(url, verify=False,timeout=3).content, "html.parser")

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
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
                if len(href.split('/')) > 4:
                    if not str(href).endswith('.apk'):
                        print(href)
                        try:
                            soup_ex_link = BeautifulSoup(requests.get(href, verify=False,timeout=3).content, "html.parser")
                            text = get_html(soup_ex_link)
                            external_urls.add(f"{href}")
                            external_urls_test.append(f"{href}")
                            page_text.append(text)
                            print('page text ok',href)
                        except:
                            external_urls.add(f"{href}")
                            external_urls_test.append(f"{href}")
                            page_text.append(np.nan)
                            print('page text nan', href)
            continue
        # print(f"{GREEN}[*] Внутренняя ссылка: {href}{RESET}")
        urls.add(f"{href}")
        internal_urls.add(href)
    return list(external_urls_test), page_text

def create_dataframe(links, text, itteration):
    """
        Создает DataFrame из списков ссылок, текста и номера итерации.
    """
    data = {
        'link': links,
        'text': text,
        'itteration': itteration
    }
    df = pd.DataFrame(data)
    return df

def pars_duck(name, period):

    print('Duck')
    url = 'https://duckduckgo.com/'
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    driver.find_element(By.ID, "searchbox_input").send_keys(f"{name}\n")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    df = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник'])
    for links in soup.findAll('li', {'data-layout': 'organic'}):
        for links_1 in links.findAll('div', {'class': 'ikg2IXiCD14iVX7AdZo1'}):
            # print(links_1.find('a').get('href'))
            df_row = pd.DataFrame(
                {'Описание': [name], 'Ссылка': [f'{links_1.find("a").get("href")}'], 'Источник': ['Google'],
                 'Дата': period})
            df = pd.concat([df, df_row])
    return df

@app1_blueprint.route('/pars')
def parse():

    n_count = 2  # количество итераций

    name = request.args.get('username')
    period = datetime.datetime.now()

    df_new = pd.DataFrame(columns=['Описание', 'Ссылка', 'Источник', 'Дата'])
    df_new = pd.concat([df_new, pars_duck(name, period)])

    # Список начальных URL для итерации
    list_iterration = list(set(df_new['Ссылка']))
    # list_iterration = ['https://www.marronnier.ru/blog/15-analitika/52-avtomatizitsiya-klasterizatsiya-klyuchevyh-slov-na-python']
    print(list_iterration)

    df_summary = pd.DataFrame(columns=['link', 'text', 'itteration'])
    itteration = 1


    # Первая итерация
    for i in tqdm(list_iterration, ncols=100):
        try:
            first_row_text = get_html_with_delay(i)
            df_summary.loc[len(df_summary.index)] = [i, first_row_text, 1]
            links, text = get_all_website_links(i)
            df = create_dataframe(links, text, 2)
            df_summary = pd.concat([df_summary, df], ignore_index=True)
        except:
            pass


    itteration += 1

    #
    # # Следующие итерации до n_count
    # while n_count >= itteration:
    #     df = df_summary.loc[(df_summary['Ittrertion'] == itteration)]
    #
    #     for i in df['Link']:
    #         links, text = get_all_website_links(i)
    #         df_new = create_dataframe(links, text, itteration + 1)
    #         df_summary = pd.concat([df_summary, df_new], ignore_index=True)
    #
    #     itteration += 1
    #
    # # Вывод результата

    df_summary.dropna(subset='text',inplace=True)


    df_summary = rake_nltk()
    print(df_summary)
    print(df_summary.info())


    # redirect('/app2/keywords')

    df_summary.to_pickle('table_show.pkl')
    # df_summary.to_sql(TABLE_NAME, engine, if_exists='append', chunksize=1000, index=False, schema=SCHEMA_NAME)
    return redirect('/app2/table')

