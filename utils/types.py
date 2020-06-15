from typing import Any


class DictWithAttrs(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError('Нет такого аттрибута:' + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError('Нет такого атрибута: ' + name)


class GlobalObject:
    """
    Класс глобальных объектов с одним лишь геттером-сеттером и одним атрибутом.
    Не знаю, что тут рассказывать. Пойду, лучше, поем.
    """
    def __init__(self, value: Any):
        """
        :param value: собсна, значение для инициализации
        """
        self._value = value

    @property
    def value(self) -> Any:
        """
        :return: чоу положили, то и вернет, без всякой там самодеятельности
        """
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._value = value
