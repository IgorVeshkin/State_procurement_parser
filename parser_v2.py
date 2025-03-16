import time

from bs4 import BeautifulSoup

from selenium import webdriver

import xmltodict


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

    # Закрываю соединение, закрываю браузер
    driver.close()

    return body

def parse_xml_data(local_url, wait=0, step=1):
    if step == 5:
        return 'Не удалось получить данные'

    # Создаю объект selenuim
    driver = webdriver.Edge()

    # Перехожу на сайт
    driver.get(local_url)

    time.sleep(wait)

    # Передаю html-код страницы в BeautifulSoup и создаю объект на основе полученных данных
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Закрываю соединение, закрываю браузер
    driver.close()

    # Получаю тело страницы
    body = soup.body

    if '404 Not Found' in str(body):
        print(f'Выполняю загрузки страницы еще раз (шаг {step})...')

        return parse_xml_data(local_url, wait, step+1)

    xml_data = body.find('div', {'id': 'folder0'}).text

    return str(xml_data)


def main():

    # https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on
    # https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber=1

    root_url = 'https://zakupki.gov.ru'

    base_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber='


    for page_index in range(1, 4): # 11
        if page_index not in (1, 2):
            url = base_url + str(page_index)

            print('Страница парсинга:', url)

            # Парсинг ссылок на печатную форму
            body = parse_data(url, 0)

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

                xml_content = parse_xml_data(xml_url, 4)

                if xml_content == 'Не удалось получить данные':
                    print(xml_content)
                    continue

                parsed_xml_content = xmltodict.parse(xml_content)
                xml_dict = parsed_xml_content[next(iter(parsed_xml_content.keys()))]['commonInfo']

                print(f'{xml_url} | xml для {index} записи:', xml_dict['publishDTInEIS'])


            print('_'*70, end='\n\n')


if __name__ == '__main__':
    main()
