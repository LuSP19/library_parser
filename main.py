from pathlib import Path

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


def main():
    page_url_pattern = 'https://tululu.org/b{0}/'
    file_url_pattern = 'https://tululu.org/txt.php?id={0}'
    
    for book_id in range(1,11):
        page_url = page_url_pattern.format(book_id)
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.find('h1').text.split('::')[0].strip()
    
        file_url = file_url_pattern.format(book_id)
        filepath = download_txt(file_url, f'{book_id}. {title}')
        print(filepath) if filepath else None


if __name__ == '__main__':
    main()
