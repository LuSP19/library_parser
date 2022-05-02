import argparse
from pathlib import Path
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
    try:
        check_for_redirect(response)

        Path(folder).mkdir(exist_ok=True)
        filepath = Path(folder, sanitize_filename(f'{filename}.txt'))
        with open(filepath, 'wb') as file:
            file.write(response.content)

        return filepath
    except requests.exceptions.HTTPError:
        pass


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_redirect(response)

        Path(folder).mkdir(exist_ok=True)
        filename = unquote(urlsplit(url)[2].split('/')[-1])
        filepath = Path(folder, filename)
        with open(filepath, 'wb') as file:
            file.write(response.content)

        return filepath
    except requests.exceptions.HTTPError:
        pass


def parse_book_page(content):
    soup = BeautifulSoup(content, 'lxml')
    title, author = list(map(str.strip, soup.find('h1').text.split('::')))
    genres = [
        tag.text
        for tag
        in soup.find('div', {'id': 'content'}).find(
            'span', class_='d_book'
        ).find_all('a', href=True)
    ]
    image_url = urljoin(
        'https://tululu.org/',
        soup.find(class_='bookimage').find('img')['src']
    )
    comments = '\n'.join([
        tag.find(class_='black').text
        for tag in soup.find_all(class_='texts')
    ])

    return {
        'title': title,
        'author': author,
        'genres': genres,
        'image_url': image_url,
        'comments': comments,
    }


def main():
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

    for book_id in range(args.start_id, args.end_id + 1):
        page_url = page_url_pattern.format(book_id)
        response = requests.get(page_url)
        response.raise_for_status()
        try:
            check_for_redirect(response)
            book = parse_book_page(response.text)

            payload = {'id': book_id}
            filepath = download_txt(
                base_file_url, payload, f'{book_id}. {book["title"]}'
            )
            if filepath:
                download_image(book['image_url'])
                print('Название:', book['title'])
                print('Автор:', book['author'])
                print()
        except requests.exceptions.HTTPError:
            pass


if __name__ == '__main__':
    main()
