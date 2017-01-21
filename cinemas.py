import requests
import time
import re
from collections import Counter
from bs4 import BeautifulSoup
from argparse import ArgumentParser


def fetch_html_page(url, payload={}):
    return requests.get(url, payload).text


def parse_afisha_page(raw_html):
    html_parser = BeautifulSoup(raw_html, 'html.parser')
    movie_template = re.compile('www.afisha.ru/movie/\d+/')
    cinema_template = re.compile('www.afisha.ru/[a-z]+/cinema/\d+/')
    movies = {}
    for link in html_parser.find_all('a'):
        href = link.get('href')
        if movie_template.search(href):
            movie_title = link.string
            continue
        if cinema_template.search(href):
            if movie_title not in movies:
                movies[movie_title] = Counter()
            movies[movie_title]['count_cinemas'] += 1
    return movies


def parse_kinopoisk_page(raw_html):
    html_parser = BeautifulSoup(raw_html, 'html.parser')
    votes_template = re.compile('/film/\d+/votes')
    for link in html_parser.find_all('a'):
        href = link.get('href')
        if href and votes_template.search(href):
            rating_ball = float(link.contents[1].string)
            rating_count = link.contents[3].string
            return rating_ball, rating_count
    return 0.0, 0


def delete_art_house_movies(movies, min_count_cinemas):
    not_art_house_movies = {}
    for movie_title in movies:
        if movies[movie_title]['count_cinemas'] >= min_count_cinemas:
            not_art_house_movies[movie_title] = movies[movie_title]
    return not_art_house_movies


def fetch_movies_title_from_afisha():
    url = 'http://www.afisha.ru/msk/schedule_cinema/'
    raw_html = fetch_html_page(url)
    movies = parse_afisha_page(raw_html)
    return movies


def find_movies_rating(movies):
    url = 'https://www.kinopoisk.ru/index.php'
    payload = {'first': 'yes'}
    for movie_title in movies:
        payload['kp_query'] = movie_title
        raw_html = fetch_html_page(url, payload)
        rating_ball, rating_count = parse_kinopoisk_page(raw_html)
        movies[movie_title]['rating_ball'] = rating_ball
        movies[movie_title]['rating_count'] = rating_count
        time.sleep(20)


def sorted_movies_by_rating(movies):
    sorted(movies,
           key=lambda movie_title: (movies[movie_title]['rating_ball']))


def output_movies_to_console(movies, count_popular_movies):
    for movie_title in list(movies.keys())[:count_popular_movies]:
        count_cinemas = movies[movie_title]['count_cinemas']
        rating_ball = movies[movie_title]['rating_ball']
        output_string = 'Фильм "%s" имеет рейтинг %.3f, его показывают в %d кинотеатрах'
        print(output_string % (movie_title, rating_ball, count_cinemas))


if __name__ == '__main__':
    parser = ArgumentParser(prog='cinemas',
                            description='Поиск популярных фильмов, идущих в прокате')
    parser.add_argument('--count_popular_movies', default=10, type=int,
                        help='количество популярных фильмов для вывода в консоль')
    parser.add_argument('--count_cinemas', default=0, type=int,
                        help='минимальное количество кинотеатров, в которых идёт фильм')
    program_args = parser.parse_args()
    count_popular_movies = program_args.count_popular_movies
    count_cinemas = program_args.count_cinemas
    movies = fetch_movies_title_from_afisha()
    if count_cinemas:
        movies = delete_art_house_movies(movies, count_cinemas)
    find_movies_rating(movies)
    sorted_movies_by_rating(movies)
    output_movies_to_console(movies, count_popular_movies)
