_MARKDOWN_CHARACTERS = '#*-+>`[]()_~!'


def de_markdown(string) -> str:
    """
    Возвращает строку с экранированными специальными символами маркдауна
    :param string:
    :return:
    """
    if not isinstance(string, str):
        string = str(string)
    for character in _MARKDOWN_CHARACTERS:
        string = string.replace(character, '\\' + character)
    return string


__all__ = ['de_markdown']
