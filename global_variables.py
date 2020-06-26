from utils.types import GlobalObject

RUNNING_FLAG = GlobalObject(True)
# Экземпляр, которым пользуется диспетчер чтобы останавливать свой бесконечный цикл. Сначала хотел сделать так:
# _RUNNING_FLAG = GlobalObject(True)
# RUNNING_FLAG = _RUNNING_FLAG.value
# но не прокатило, не фортануло: RUNNING_FLAG не импортируется. Приходится обращаться к значению через геттер-сеттер
TELEGRAM_BOT = GlobalObject(None)
# А этот парень нужен для того, чтобы вернуть экземпляр класса Bot для взаимодействия с ним
# Тоже жуткий костыль

__all__ = ['RUNNING_FLAG', 'TELEGRAM_BOT']
