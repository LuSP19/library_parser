from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.exceptions.HTTPError()


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url)
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


def main():
    page_url_pattern = 'https://tululu.org/b{0}/'
    file_url_pattern = 'https://tululu.org/txt.php?id={0}'

    for book_id in range(1, 11):
        page_url = page_url_pattern.format(book_id)
        response = requests.get(page_url)
        response.raise_for_status()
        try:
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.find('h1').text.split('::')[0].strip()
            comments = '\n'.join([
                tag.find(class_='black').text
                for tag in soup.find_all(class_='texts')
            ])

            file_url = file_url_pattern.format(book_id)
            filepath = download_txt(file_url, f'{book_id}. {title}')
            if filepath:
                image_url = urljoin(
                    'https://tululu.org/',
                    soup.find(class_='bookimage').find('img')['src']
                )
                download_image(image_url)
                print('Заголовок:', title)
                print(image_url)
                print(comments)
        except requests.exceptions.HTTPError:
            pass


if __name__ == '__main__':
    main()
