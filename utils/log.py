"""
Модуль логописательства.
log -- написать сообщение в лог файл
"""
import datetime


def log(message: str, filename: str = 'logfile.log') -> None:
    """
    Добавить сообщение к лог-файлу
    :param message: собственно сообщение
    :param filename: имя лог-файла
    :return: None
    """
    dt = datetime.datetime.utcnow()
    dt = dt.isoformat(sep=' ', timespec='seconds')
    message = '[{} + 00:00]: {}'.format(dt, message)
    message += '\n'
    print(message)
    with open(filename, 'a') as logfile:
        logfile.write(message)
