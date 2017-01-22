import requests
import time
import re
from bs4 import BeautifulSoup
from argparse import ArgumentParser


TIME_DELAY_SECONDS = 20


def fetch_html_page(url, payload=None):
    return requests.get(url, payload).text


def parse_afisha_page(raw_html):
    html_parser = BeautifulSoup(raw_html, 'html.parser')
    movie_template = re.compile('www.afisha.ru/movie/\d+/')
    cinema_template = re.compile('www.afisha.ru/[a-z]+/cinema/\d+/')
    movies = []
    for link in html_parser.find_all('table'):
        count_cinemas = len(link.find_all(href=cinema_template))
        if count_cinemas:
            movie_title = link.find_parent().find(href=movie_template).string
            movies.append({})
            movies[-1]['movie_title'] = movie_title
            movies[-1]['count_cinemas'] = count_cinemas
    return movies


def parse_kinopoisk_page(raw_html):
    html_parser = BeautifulSoup(raw_html, 'html.parser')
    votes_template = re.compile('/film/\d+/votes')
    rating_ball = 0.0
    rating_count = 0
    for link in html_parser.find_all(href=votes_template):
        rating_ball = float(link.contents[1].string)
        rating_count = link.contents[3].string
        break
    return rating_ball, rating_count


def delete_art_house_movies(movies, min_count_cinemas):
    not_art_house_movies = []
    for movie in movies:
        if movie['count_cinemas'] >= min_count_cinemas:
            not_art_house_movies.append(movie)
    return not_art_house_movies


def fetch_movies_title_from_afisha():
    url = 'http://www.afisha.ru/msk/schedule_cinema/'
    raw_html = fetch_html_page(url)
    movies = parse_afisha_page(raw_html)
    return movies


def find_movies_rating(movies):
    url = 'https://www.kinopoisk.ru/index.php'
    payload = {'first': 'yes'}
    for movie in movies:
        payload['kp_query'] = movie['movie_title']
        raw_html = fetch_html_page(url, payload)
        rating_ball, rating_count = parse_kinopoisk_page(raw_html)
        movie['rating_ball'] = rating_ball
        movie['rating_count'] = rating_count
        time.sleep(TIME_DELAY_SECONDS)


def sort_movies_by_rating(movies):
    sorted(movies, key=lambda movie: movie['rating_ball'])


def output_movies_to_console(movies, count_popular_movies=0):
    if not count_popular_movies:
        count_popular_movies = len(movies)
    for movie in movies[:count_popular_movies]:
        movie_title = movie['movie_title']
        count_cinemas = movie['count_cinemas']
        rating_ball = movie['rating_ball']
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
    sort_movies_by_rating(movies)
    output_movies_to_console(movies, count_popular_movies)
