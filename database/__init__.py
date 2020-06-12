"""
Модуль рулежки базой данных.
Функции:
raw_request -- посылка сырого запроса базе данных, а-ля 'SELECT * FROM table'
create_table -- создание таблицы, если она еще не
select -- SELECT с более человеческим лицом
add_column -- добавляет столбец в таблицу, если он еще не
insert -- строку в таблицу
update -- обновляет поля в таблице
"""
import sqlite3
from typing import Optional, Union
from config import DATABASE, BOT_OWNER_ID


def _column_in_table(table: str, column: str) -> bool:
    """
    Проверяет есть ли столбец в таблице
    :param table: имя таблицы
    :param column: имя столбца
    :return: None
    """
    request = 'PRAGMA TABLE_INFO({})'.format(table)
    response = raw_request(request)
    for columns in response:
        if columns[1] == column:
            return True
    return False


def _convert_value(value: Union[str, int, float]) -> Union[str, int, float]:
    """
    Делает из 'строки' '"строку"', либо возвращает int и float без изменений,
    либо вызывает ошибку
    :param value: какой-то str, int или float
    :return: int, float или модифицированный str
    """
    if isinstance(value, str):
        return '"{}"'.format(value)
    elif isinstance(value, int) or isinstance(value, float):
        return value
    else:
        vt = type(value)
        raise AssertionError('Значения столбцов могут быть только типов str, int и float, а здесь {}!'.format(vt))


def raw_request(request: str, save: bool = False, database: str = DATABASE) -> Optional[list]:
    """
    Выполняет сырой запрос к базе данных, типа 'SELECT * FROM table'
    :param request: запрос
    :param save: сохранять ли базу данных после запроса
    :param database: файл базы данных
    :return: список кортежей ответа или None, если save=True
    """
    connect = sqlite3.connect(database)
    cursor = connect.cursor()
    if save:
        cursor.execute(request)
        connect.commit()
        answer = None
    else:
        answer = cursor.execute(request).fetchall()
    connect.close()
    return answer


def create_table(table: str, database: str = DATABASE, **columns_and_defaults: Union[str, int, float]) -> None:
    """
    Создает таблицу в базе данных с обязательным столбцом id, если ее еще нет
    :param table: имя таблицы
    :param database: файл базы данных
    :param columns_and_defaults: **kwargs вида столбец=значение_по_умолчанию
    :return: None
    """
    request = 'CREATE TABLE IF NOT EXISTS {} (id INTEGER NOT NULL PRIMARY KEY)'.format(table)
    raw_request(request, save=True, database=database)
    for column, default in columns_and_defaults.items():
        add_column(table, column, default=default, database=database)


def select(table: str, *selection: str, database: str = DATABASE, condition: Optional[str] = None) -> list:
    """
    Делает 'SELECT ... FROM ... WHERE ...'
    :param table: имя таблицы
    :param selection: *args столбцов, из которых будет производиться выборка
    :param database: файл базы данных
    :param condition: условие на языке SQL, которое будет после WHERE, если None -- WHERE не пойдет в запрос
    :return: список кортежей ответа
    """
    if selection:
        selection = ', '.join(selection)
    else:
        selection = '*'
    request = 'SELECT {} FROM {}'.format(selection, table)
    if condition is not None:
        request += ' WHERE {}'.format(condition)
    answer = raw_request(request, database=database)
    return answer


def add_column(table: str, column: str, default: Union[str, int, float, None] = None, database: str = DATABASE) -> None:
    """
    Добавляет столбец в таблицу, если он еще не
    :param table: имя таблицы
    :param column: название столбца
    :param default: значение по умолчанию
    :param database: файл базы данных
    :return: None
    """
    if default is None:
        column_type = 'TEXT'
        default = '""'
    elif isinstance(default, str):
        column_type = 'TEXT'
        default = '"{}"'.format(default)
    elif isinstance(default, int):
        column_type = 'INTEGER'
    elif isinstance(default, float):
        column_type = 'REAL'
    else:
        raise AssertionError('default может быть только типов str, int, float, а здесь {}!'.format(type(default)))
    if not _column_in_table(table, column):
        request = 'ALTER TABLE {} ADD COLUMN {} {} NOT NULL DEFAULT {}'.format(table, column, column_type, default)
        raw_request(request, save=True, database=database)


def insert(table: str, row_id: int, database: str = DATABASE, **columns_and_values: Union[str, int, float]) -> None:
    """
    Вставляет строку в таблицу, с обязательным уникальным значением для столбца id
    :param table: имя таблицы
    :param row_id: значение, которое будет вставлено в столбец id
    :param database: файл базы данных
    :param columns_and_values: **kwargs вида столбец=значение
    :return: None
    """
    if not columns_and_values:
        raise AssertionError('Не указаны столбцы и значения!')
    request = 'INSERT INTO {} ({}) VALUES ({})'
    columns = ['id']
    values = [str(row_id)]
    for key, value in columns_and_values.items():
        columns.append(key)
        value = _convert_value(value)
        values.append(str(value))
    columns = ', '.join(columns)
    values = ', '.join(values)
    request = request.format(table, columns, values)
    raw_request(request, save=True, database=database)


def update(table: str, condition: str, database: str = DATABASE, **columns_and_values: Union[str, int, float]) -> None:
    """
    Обновляет строки с обязательным условием (ибо нефип)
    :param table: имя таблицы
    :param condition: условие на языке SQL, которое будет после WHERE
    :param database: файл базы данных
    :param columns_and_values: **kwargs вида столбец=значение. Обязателен хотя бы один.
    :return: None
    """
    if not columns_and_values:
        raise AssertionError('Не указаны столбцы и значения')
    sets = []
    for column, value in columns_and_values.items():
        value = _convert_value(value)
        sets.append('{} = {}'.format(column, value))
    sets = ', '.join(sets)
    request = 'UPDATE {} SET {} WHERE {}'.format(table, sets, condition)
    raw_request(request, save=True, database=database)


# создание таблицы юзеров
create_table('users', access_level=1)
if not select('users', condition='id = {}'.format(BOT_OWNER_ID)):
    insert('users', BOT_OWNER_ID, access_level=5)

__all__ = ['raw_request', 'create_table', 'select', 'add_column', 'insert', 'update']
