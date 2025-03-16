import xmltodict
from celery import Celery

from bs4 import BeautifulSoup
from selenium import webdriver

import time

app = Celery('celery_v1', broker='redis://localhost:1212/0', backend='redis://localhost:1212/1') # backend='db+sqlite:///celery_backend_db.sqlite3')
app.config_from_object(__name__)

# Раздельная функция
@app.task(bind=True, max_retries=5)
def parse_xml_url(self, url, wait=0):

    """
    Функция парсит данные страницы для получения xml-данных

    :param self: ссылка на саму функцию
    :param url: адрес на страницу для парсинга
    :param wait: количество секунд ожидания парсера
    :return: Возвращает xml-текст страницы
    """
    # Создаю объект selenuim
    driver = webdriver.Edge()

    # Перехожу на сайт
    driver.get(url)

    time.sleep(wait)

    # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Закрываю соединение, закрываю браузер
    driver.close()

    # Получаю тело страницы
    body = soup.body

    if '404 Not Found' in str(body):

        print('Не удалось прогрузить страницу. Перезагружаю функцию. Ожидайте 5 секунд...')
        self.retry(countdown=5 if wait==0 else wait)

    xml_data = body.find('div', {'id': 'folder0'}).text

    return str(xml_data)


# Раздельная функция
@app.task
def get_url(pages_number=10, ):
    root_url = 'https://zakupki.gov.ru'

    base_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber='

    for page_index in range(1, pages_number+1):  # 11
        # Пропускаю первые 2 страницы
        if page_index not in (1, 2):
            url = base_url + str(page_index)

            print('Страница парсинга:', url)

            # Создаю объект selenuim
            driver = webdriver.Edge()

            # Перехожу на сайт
            driver.get(url)

            # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Получаю тело страницы
            body = soup.body

            # Закрываю соединение, закрываю браузер
            driver.close()

            # Переменная для хранения ссылок на xml
            xml_urls_list = []

            # Получаю все печатные формы на странице
            publishing_forms = body.find_all('div', {'class': 'registry-entry__header-top__icon'})

            for publishing_form in publishing_forms:
                publishing_for_urls = publishing_form.find_all('a')

                # Получаю нужную ссылку
                for link in publishing_for_urls:
                    if 'view.html' in link['href']:
                        xml_urls_list.append(root_url + link['href'].replace('view.html', 'viewXml.html'))

            return xml_urls_list



@app.task(bind=True, max_retries=5)
def parse_xml_url_for_date(self, url, wait=0):
    """
    Функция парсит данные страницы для получения xml-данных

    :param self: ссылка на саму функцию
    :param url: адрес на страницу для парсинга
    :param wait: количество секунд ожидания парсера
    :return: Строку с ссылкой на страницу парсинга и дату спарсенную со страницу в формате xml
    """
    # Создаю объект selenuim
    driver = webdriver.Edge()

    # Перехожу на сайт
    driver.get(url)

    time.sleep(wait)

    # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Закрываю соединение, закрываю браузер
    driver.close()

    # Получаю тело страницы
    body = soup.body

    if '404 Not Found' in str(body):
        print('Не удалось прогрузить страницу. Перезагружаю функцию. Ожидайте 5 секунд...')
        self.retry(countdown=5 if wait == 0 else wait)

    xml_data = body.find('div', {'id': 'folder0'}).text

    parsed_xml_content = xmltodict.parse(xml_data)
    xml_dict = parsed_xml_content[next(iter(parsed_xml_content.keys()))]['commonInfo']

    return f'{url}: {xml_dict['publishDTInEIS']}'


@app.task
def parse_all_data(pages_number=10,):
    """
    Функция парсит ссылки печатных форм. Во время выполнения данной задачи, в очередь на выполнение добавляются задачи парсинга xml-данных печатной формы по мере получения ссылок в рамках данной функции

    :param pages_number: Количество страниц, которое необходимо спарсить
    :return: Список url печатных форм
    """

    root_url = 'https://zakupki.gov.ru'

    base_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber='

    for page_index in range(1, pages_number+1):  # 11
        # Пропускаю первые 2 страницы
        if page_index not in (1, 2):
            url = base_url + str(page_index)

            print('Страница парсинга:', url)

            # Создаю объект selenuim
            driver = webdriver.Edge()

            # Перехожу на сайт
            driver.get(url)

            # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Получаю тело страницы
            body = soup.body

            # Закрываю соединение, закрываю браузер
            driver.close()

            # Переменная для хранения ссылок на xml
            xml_urls_list = []

            # Получаю все печатные формы на странице
            publishing_forms = body.find_all('div', {'class': 'registry-entry__header-top__icon'})

            for publishing_form in publishing_forms:
                publishing_for_urls = publishing_form.find_all('a')

                # Получаю нужную ссылку
                for link in publishing_for_urls:
                    if 'view.html' in link['href']:
                        xml_url = root_url + link['href'].replace('view.html', 'viewXml.html')

                        # Запускаю задачу для парсинга страницы xml (добовляю их в очередь)
                        parse_xml_url_for_date.delay(url=xml_url, wait=5)

                        xml_urls_list.append(xml_url)


            return xml_urls_list