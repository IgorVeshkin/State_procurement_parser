import time

from bs4 import BeautifulSoup

from selenium import webdriver

import xmltodict

import requests


def parse_data(local_url, wait):
    # Создаю объект selenuim
    driver = webdriver.Edge()

    # Перехожу на сайт
    driver.get(local_url)

    time.sleep(wait)

    # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Получаю тело страницы
    body = soup.body

    # print(str(body))

    # Закрываю соединение, закрываю браузер
    driver.close()

    return str(body)


def main():

    # https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on
    # https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber=1

    root_url = 'https://zakupki.gov.ru'

    base_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber='


    for page_index in range(1, 11): # 11
        # Пропускаю первые 2 страницы
        if page_index not in (1, 2):
            url = base_url + str(page_index)

            print('Страница парсинга:', url)

            response = requests.get(url)

            soup = BeautifulSoup(response.text, 'html.parser')

            body = soup.body

            if '404 Not Found' in str(body):
                print('Не удалось прогрузить страницу. Перезапустите скрипт...')
                return

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


            # Получение xml для 10 записей одной страницы
            for index, xml_url in enumerate(xml_urls_list, start=1):
                xml_data = requests.get(xml_url)

                time.sleep(2)

                xml_content = xml_data.text

                xml_content = xml_content[xml_content.find('<ns7'):]

                if xml_data.status_code != 404:

                    parsed_xml_content = xmltodict.parse(xml_content)
                    xml_dict = parsed_xml_content[next(iter(parsed_xml_content.keys()))]['commonInfo'] # ['ns7:epNotificationEZK2020'] ['ns7:epNotificationEF2020']

                    print(f'{xml_url} | xml для {index} записи:', xml_dict['publishDTInEIS'])

                else:
                    print('Данный не были получены (Ошибка 404). Перезагружаю страницу...')

                    xml_data_iter_2 = requests.get(xml_url)

                    xml_content_iter_2 = xml_data_iter_2.text

                    xml_content_iter_2 = xml_content_iter_2[xml_content_iter_2.find('<ns7'):]

                    time.sleep(2)

                    if xml_data_iter_2.status_code != 404:
                        parsed_xml_content_iter_2 = xmltodict.parse(xml_content_iter_2)
                        xml_dict_iter_2 = parsed_xml_content_iter_2[next(iter(parsed_xml_content_iter_2.keys()))]['commonInfo'] # ['ns7:epNotificationEZK2020'] ['ns7:epNotificationEF2020']
                        print(f'{xml_url} | xml для {index} записи:', xml_dict_iter_2['publishDTInEIS'])
                        continue

                    print('Не удалось получить данные при повторном запуске (Ошибка 404). Перехожу к следующей ссылке...')
                    print(f'{xml_url} | xml для {index} записи:', None)


            print('_'*70, end='\n\n')


if __name__ == '__main__':
    main()

