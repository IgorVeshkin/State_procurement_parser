from pprint import pprint

from celery_v1 import *


if __name__ == '__main__':
    get_data_task = parse_all_data.delay(pages_number=4)

    print('Ожидайте завершения задачи и вывода результата...\n')
    while get_data_task.status == 'PENDING':
        continue

    if get_data_task.ready():
        print('ID задачи:', get_data_task.task_id)
        print('Статус задачи:', get_data_task.status)

        print('Данные задачи:' )
        pprint(get_data_task.get())
