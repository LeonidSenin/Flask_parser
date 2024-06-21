from flask import Blueprint,redirect
import nltk
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
from rake_nltk import Rake
import string
import re
import pandas as pd
from collections import Counter

# app2_blueprint = Blueprint('app2', __name__)

# nltk.download('stopwords')
patterns = "[A-Za-z0-9!#$%&'()*+,./:;<=>?@[\]^_`{|}~—\"\-]+"
stopwords_ru = stopwords.words("russian")
morph = MorphAnalyzer()

def preprocess_text(text):
    # Приведение текста к нижнему регистру и удаление пунктуации
    text = str(text).lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

def get_phrase_frequency(text, phrases):
    # Разбиение текста на слова
    words = text.split()

    # Подсчет частоты встречаемости фраз в тексте
    phrase_counter = Counter()
    for phrase in phrases:
        phrase_words = phrase.split()
        phrase_length = len(phrase_words)

        for i in range(len(words) - phrase_length + 1):
            if words[i:i + phrase_length] == phrase_words:
                phrase_counter[phrase] += 1

    return phrase_counter

def lemmatize(text):
    '''Функция:
    - избавимся от букв латинского алфавита, чисел, знаков препинания и всех символов, например, символ @ встречается почти везде;
    - разобьем пост на токены;
    - проведем лемматизацияю, получив нормальную (начальную) форму слова;
    - удалим стоп-слова.
    '''
    doc = re.sub(patterns, ' ', text)
    tokens = []
    for token in doc.split():
        if token and token not in stopwords_ru:
            token = token.translate(str.maketrans('', '', string.punctuation))
            token = token.strip()
            token = morph.normal_forms(token)[0]
            tokens.append(token)
    if len(tokens) > 2:
        return ' '.join(tokens)
    return ''
def extract_keywords(text, stop_words=stopwords_ru, min_score=4.0, min_word_length=4, min_phrase_length=3,max_phrase_length=4, min_phrase_freq=2):
    # Предобработка текста
    # processed_text = lemmatize(text)
    # processed_text = preprocess_text(text)
    processed_text = preprocess_text(text)

    # Создание экземпляра Rake с пользовательскими или стандартными стоп-словами
    rake_nltk_var = Rake(stopwords=stop_words,include_repeated_phrases=False,min_length=min_phrase_length,max_length=max_phrase_length) \
        if stop_words else Rake(include_repeated_phrases=False,min_length=min_phrase_length,max_length=max_phrase_length)

    # Извлечение ключевых фраз из текста
    rake_nltk_var.extract_keywords_from_text(processed_text)

    # Получение ранжированных фраз с их скором
    keyword_extracted = rake_nltk_var.get_ranked_phrases_with_scores()

    # Получение частоты встречаемости каждой фразы
    # phrases = [phrase for _, phrase in keyword_extracted]
    # phrase_freq = get_phrase_frequency(processed_text, phrases)

    # Фильтрация ключевых фраз по условиям
    filtered_keywords = [
        (score, phrase) for score, phrase in keyword_extracted
        if score >= min_score
           and all(len(word) >= min_word_length for word in phrase.split())
           and min_phrase_length <= len(phrase.split()) <= max_phrase_length
           # and phrase_freq[phrase] >= min_phrase_freq
    ]

    return filtered_keywords

def display_keywords(keywords):
    for score, keyword in keywords:
        print(f"{keyword}: {score}")

# @app2_blueprint.route('/keywords')
def rake_nltk():

    df_summary = pd.read_pickle('table.pkl')
    # Rake
    # df_summary['Text'] = df_summary['Text'].apply(lambda x: lemmatize(x))
    df_summary['rare_text'] = df_summary['text'].apply(lambda x: extract_keywords(x,
        stop_words=stopwords_ru,
        min_score=3.0,
        min_word_length=1,
        min_phrase_length=3,
        max_phrase_length =5,
        min_phrase_freq=2))

    df_summary['rare_text'] = df_summary['rare_text'].apply(lambda x: sorted(list(set(x)), reverse=True))

    # df_summary.to_pickle('table_show.pkl')
    return df_summary
    # return redirect('/app3/table')