import sqlite3
from config import DATABASE, BOT_OWNER_ID


def _column_in_table(table, column):
    request = 'PRAGMA TABLE_INFO({})'.format(table)
    response = raw_request(request)
    for columns in response:
        if columns[1] == column:
            return True
    return False


def _convert_value(value):
    if isinstance(value, str):
        return '"{}"'.format(value)
    elif isinstance(value, int) or isinstance(value, float):
        return value
    else:
        vt = type(value)
        raise AssertionError('Значения столбцов могут быть только типов str, int и float, а здесь {}!'.format(vt))


def raw_request(request, save=False, database=DATABASE):
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


def create_table(table, database=DATABASE, **columns_and_defaults):
    request = 'CREATE TABLE IF NOT EXISTS {} (id INTEGER NOT NULL PRIMARY KEY)'.format(table)
    raw_request(request, save=True, database=database)
    for column, default in columns_and_defaults.items():
        add_column(table, column, default=default, database=database)


def select(table, *selection, database=DATABASE, condition=None):
    if selection:
        selection = ', '.join(selection)
    else:
        selection = '*'
    request = 'SELECT {} FROM {}'.format(selection, table)
    if condition is not None:
        request += ' WHERE {}'.format(condition)
    answer = raw_request(request, database=database)
    return answer


def add_column(table, column, default=None, database=DATABASE):
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


def insert(table, row_id, database=DATABASE, **columns_and_values):
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


def update(table, condition, database=DATABASE, **columns_and_values):
    if not columns_and_values:
        raise AssertionError('Не указаны столбцы и значения')
    sets = []
    for column, value in columns_and_values.items():
        value = _convert_value(value)
        sets.append('{} = {}'.format(column, value))
    sets = ', '.join(sets)
    request = 'UPDATE {} SET {} WHERE {}'.format(table, sets, condition)
    raw_request(request, save=True, database=database)


create_table('users', access_level=1)
if not select('users', condition='id = {}'.format(BOT_OWNER_ID)):
    insert('users', BOT_OWNER_ID, access_level=5)

__all__ = ['raw_request', 'create_table', 'select', 'add_column', 'insert', 'update']
