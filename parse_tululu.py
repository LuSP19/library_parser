import argparse
import sys
from pathlib import Path
from time import sleep
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.exceptions.HTTPError()


def download_txt(url, payload, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)

    Path(folder).mkdir(exist_ok=True)
    filepath = Path(folder, sanitize_filename(f'{filename}.txt'))
    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def download_image(url, addendum, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    Path(folder).mkdir(exist_ok=True)
    path = urlsplit(url)[2]
    filename = path.split('/')[-1]
    filename = unquote(filename)
    filename = Path(filename)
    unique_filename = '{0}_{2}{1}'.format(
        filename.stem, filename.suffix, addendum
    )
    filepath = Path(folder, unique_filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def parse_book_page(content, base_url):
    soup = BeautifulSoup(content, 'lxml')
    title, author = list(map(str.strip, soup.find('h1').text.split('::')))
    genre_tags = soup.find(
        'div', {'id': 'content'}
    ).find('span', class_='d_book').find_all('a', href=True)
    genres = []
    for tag in genre_tags:
        genres.append(tag.text)
    image_url = urljoin(
        base_url,
        soup.find(class_='bookimage').find('img')['src']
    )
    comment_tags = soup.find_all(class_='texts')
    comments = []
    for tag in comment_tags:
        comments.append(tag.find(class_='black').text)
    comments = '\n'.join(comments)

    return {
        'title': title,
        'author': author,
        'genres': genres,
        'image_url': image_url,
        'comments': comments,
    }


def main():
    timeouts = [1, 2, 4, 8]
    page_url_pattern = 'https://tululu.org/b{0}/'
    base_file_url = 'https://tululu.org/txt.php'

    parser = argparse.ArgumentParser(
        description='Скачивание книг с tululu.org',
    )
    parser.add_argument(
        '-s',
        '--start_id',
        help='id книги, с которой начать',
        default=1,
        type=int,
    )
    parser.add_argument(
        '-e',
        '--end_id',
        help='id книги, которой закончить',
        default=10,
        type=int,
    )

    args = parser.parse_args()

    book_id = args.start_id
    retry = 0

    while book_id < args.end_id + 1:
        page_url = page_url_pattern.format(book_id)
        try:
            response = requests.get(page_url)
            response.raise_for_status()
            check_for_redirect(response)
            book = parse_book_page(response.text, page_url)

            payload = {'id': book_id}
            filepath = download_txt(
                base_file_url, payload, f'{book_id}. {book["title"]}'
            )
            if filepath:
                download_image(book['image_url'], book_id)
            book_id += 1
            retry = 0
        except requests.exceptions.HTTPError:
            print('HTTP error', file=sys.stderr)
            book_id += 1
        except requests.exceptions.ConnectionError:
            print('Connection error', file=sys.stderr)
            sleep(timeouts[retry])
            retry += 1
            if retry > len(timeouts) - 1:
                print('Check your connection', file=sys.stderr)
                break


if __name__ == '__main__':
    main()
