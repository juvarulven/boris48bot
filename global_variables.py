"""
Модуль глобальных переменных. Нужен для того, чтобы пропихивать значения в другие модули,
где делать это через явную передачу мне почему-то не хотелось.
Метод, конечно, немного ректальный, но работает. А ничего лучше я не придумал.
"""
from typing import Any


class GlobalObject:
    """
    Собственно сам класс глобальных объектов с одним лишь геттером-сеттером и одним атрибутом.
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


RUNNING_FLAG = GlobalObject(True)
# Экземпляр, которым пользуется диспетчер чтобы останавливать свой бесконечный цикл. Сначала хотел сделать так:
# _RUNNING_FLAG = GlobalObject(True)
# RUNNING_FLAG = _RUNNING_FLAG.value
# но не прокатило, не фортануло: RUNNING_FLAG не импортируется. Приходится обращаться к значению через геттер-сеттер

__all__ = ['RUNNING_FLAG']