from typing import NamedTuple, List


class VaultPluginException(Exception):
    def __init__(self, message):
        super(VaultPluginException, self).__init__('VaultPlugin: ', message)


class DBDocumentFields(NamedTuple):
    """
    Поля документа базы данных.
    """
    title: str
    timestamp: str
    subscribers: List[int]


class VaultCommentsBlock(NamedTuple):
    """
    Блок комментариев пользователя Убежища
    """
    username: str
    user_url: str
    user_comments: List[str]
    with_file: bool
    post_url: str


class VaultImagePost(NamedTuple):
    """
    Пост-изображение Убежища
    """
    username: str
    user_url: str
    title: str
    post_url: str
    image_url: str
    description: str


class VaultTextPost(NamedTuple):
    """
    Текстовый пост убежища
    """
    username: str
    user_url: str
    title: str
    post_url: str
    description: str


class VaultOtherPost(NamedTuple):
    """
    Пост Убежища типа 'other'
    """
    username: str
    user_url: str
    post_url: str


class VaultAudioPost(VaultOtherPost):
    """
    Аудиопост Убежища
    """
    pass


class VaultVideoPost(VaultOtherPost):
    """
    Видеопост Убежища
    """
    pass


class VaultGodnotaPost(NamedTuple):
    """
    Пост годноты Убежища
    """
    title: str
    post_url: str
