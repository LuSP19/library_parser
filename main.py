from pathlib import Path

import requests


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.exceptions.HTTPError()


Path('books').mkdir(exist_ok=True)

url_pattern = 'https://tululu.org/txt.php?id={0}'

for book_id in range(1,11):
    url = url_pattern.format(book_id)
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_redirect(response)

        filepath = Path('books', f'{book_id}.txt')
        with open(filepath, 'wb') as file:
            file.write(response.content)
    except requests.exceptions.HTTPError:
        pass
