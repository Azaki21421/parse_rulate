import requests
from bs4 import BeautifulSoup
import json
import sqlite3
from time import time

JSON_FILE = 'bookmarks_rulate.json'
DB_FILE = 'database.db'
TABLE_NAME = 'rulate'


def get_user_credentials():
    """Получение логина и пароля от пользователя."""
    login = input('Login: ')
    password = input('Password: ')
    return login, password


def parse_ranobe(login, password):
    """Парсинг закладок с сайта Rulate."""
    url = 'https://tl.rulate.ru/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    data = {
        'login[login]': login,
        'login[pass]': password
    }
    session = requests.Session()
    session.headers.update(headers)

    response = session.post(url, data=data)
    if response.status_code == 403:
        print('Авторизация не удалась.')
        return []

    bookmarks_url = 'https://tl.rulate.ru/bookmarks'
    response = session.post(bookmarks_url, data={'type': '-1'})
    soup = BeautifulSoup(response.text, 'lxml')

    books = []
    tbody = soup.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            title_tag = row.find('a', rel='tooltip')
            title = title_tag.text.strip() if title_tag else "Нет названия"
            link = 'https://tl.rulate.ru' + title_tag['href'] if title_tag else ""
            description = title_tag['title'] if title_tag and title_tag.has_attr('title') else "Нет описания"

            chapters = row.find_all('p', class_='note')
            new_chapters = chapters[0].get_text(strip=True) if chapters else "Нет новых глав"
            opened_chapters = chapters[1].get_text(strip=True).replace("Продолжить чтение", "").strip() if len(
                chapters) > 1 else "Нет открытых глав"

            type_label = row.find(class_='type-label').text.strip() if row.find(class_='type-label') else "Нет типа"
            image_tag = row.find('img')
            image_url = 'https://tl.rulate.ru' + image_tag['src'] if image_tag else ""

            books.append({
                "title": title,
                "link": link,
                "description": description,
                "new_chapters": new_chapters,
                "opened_chapters": opened_chapters,
                "type_label": type_label,
                "image_path": image_url
            })
    return books


def save_to_json(data, filename):
    """Сохранение данных в JSON файл."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Данные сохранены в файл: {filename}")


def save_to_db(data, db_file, table_name):
    """Сохранение данных в SQLite базу данных."""
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    link TEXT,
                    description TEXT,
                    new_chapters TEXT,
                    opened_chapters TEXT,
                    type_label TEXT,
                    image_path TEXT
                )
            ''')
            for i, book in enumerate(data, start=1):
                cur.execute(f'''
                    INSERT OR REPLACE INTO {table_name} (
                        id, title, link, description, new_chapters, opened_chapters, type_label, image_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    i,
                    book['title'],
                    book['link'],
                    book['description'],
                    book['new_chapters'],
                    book['opened_chapters'],
                    book['type_label'],
                    book['image_path']
                ))
            con.commit()
        print(f"Данные сохранены в базу данных: {db_file}")
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")


def main():
    """Основная функция."""
    start_time = time()
    login, password = get_user_credentials()

    print("Начинаем парсинг...")
    books = parse_ranobe(login, password)

    if books:
        print(f"Получено {len(books)} записей.")
        save_to_json(books, JSON_FILE)
        save_to_db(books, DB_FILE, TABLE_NAME)
    else:
        print("Данных для сохранения нет.")

    elapsed_time = time() - start_time
    print(f"Скрипт выполнен за {elapsed_time:.2f} секунд.")


if __name__ == '__main__':
    main()
