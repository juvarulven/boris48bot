from typing import List, Optional, Any

_URL = 'https://vault48.org:3333/'


class Stats:
    def __init__(self, dictionary: dict):
        self.users_total: int = dictionary['users']['total']
        self.users_alive: int = dictionary['users']['alive']
        self.nodes_images: int = dictionary['nodes']['images']
        self.nodes_audios: int = dictionary['nodes']['audios']
        self.nodes_videos: int = dictionary['nodes']['videos']
        self.nodes_texts: int = dictionary['nodes']['texts']
        self.nodes_total: int = dictionary['nodes']['total']
        self.comments_total: int = dictionary['comments']['total']
        self.files_count: int = dictionary['files']['count']
        self.files_size: int = dictionary['files']['size']
        self.timestamps_boris: str = dictionary['timestamps']['boris_last_comment']
        self.timestamps_flow: str = dictionary['timestamps']['flow_last_post']


class Comments:
    def __init__(self, dictionary: dict):
        self.comments: List[Comment] = [Comment(comment) for comment in dictionary['comments']]
        self.order: str = dictionary['order']
        self.comment_count: int = dictionary['comment_count']


class Diff:
    def __init__(self, dictionary: dict):
        self.before: List[DiffPost] = [DiffPost(post) for post in dictionary['before']]
        self.after: List[DiffPost] = [DiffPost(post) for post in dictionary['after']]
        self.recent: List[DiffPost] = [DiffPost(post) for post in dictionary['recent']]
        self.heroes: List[Hero] = [Hero(hero) for hero in dictionary['heroes']]
        # self.updated = dictionary['updated']
        # self.valid = dictionary['valid']


class Comment:
    def __init__(self, dictionary: dict):
        self.id: int = dictionary['id']
        self.text: str = dictionary['text']
        self.files_order: List[str] = dictionary['files_order']
        self.created_at: str = dictionary['created_at']
        self.updated_at: str = dictionary['updated_at']
        self.deleted_at: Optional[str] = dictionary['deleted_at']
        self.files: List[File] = [File(file) for file in dictionary['files']]
        self.user: User = User(dictionary['user'])


class File:
    def __init__(self, dictionary: dict):
        self.id: int = dictionary['id']
        self.name: str = dictionary['name']
        self.orig_name: str = dictionary['orig_name']
        self.path: str = dictionary['path']
        self.full_path: str = dictionary['full_path']
        self.url: str = dictionary['url'].replace('REMOTE_CURRENT://', _URL)
        self.size: int = dictionary['size']
        self.type: str = dictionary['type']
        self.mime: str = dictionary['mime']
        self.target: str = dictionary['target']
        self.metadata: Optional[Any] = dictionary['metadata']
        self.created_at: str = dictionary['created_at']
        self.updated_at: str = dictionary['updated_at']


class BasicUser:
    def __init__(self, dictionary: dict):
        self.id: int = dictionary['id']
        self.photo: File = File(dictionary['photo'])
        self.username: str = dictionary['username']


class User(BasicUser):
    def __init__(self, dictionary: dict):
        super().__init__(dictionary)
        self.email: str = dictionary['email']
        self.role: str = dictionary['role']
        self.fullname: str = dictionary['fullname']
        self.description: Optional[str] = dictionary['description']
        self.is_activated: bool = dictionary['is_activated']
        self.last_seen: str = dictionary['last_seen']
        self.last_seen_messages: Optional[Any] = dictionary['last_seen_messages']
        self.created_at: str = dictionary['created_at']
        self.updated_at: str = dictionary['updated_at']


class BasicPost:
    def __init__(self, dictionary: dict):
        self.id: int = dictionary['id']
        self.title: int = dictionary['title']
        self.type: int = dictionary['type']
        self.created_at: int = dictionary['created_at']
        self.commented_at: int = dictionary['commented_at']
        self.thumbnail: str = dictionary['thumbnail'].replace('REMOTE_CURRENT://', _URL) if dictionary['thumbnail'] else None
        self.description: str = dictionary['description']


class DiffPost(BasicPost):
    def __init__(self, dictionary: dict):
        super().__init__(dictionary)
        self.user: User = User(dictionary['user'])


class Node(BasicPost):
    def __init__(self, dictionary: dict):
        dictionary = dictionary['node']
        super().__init__(dictionary)
        self.blocks: List[Any] = dictionary['blocks']
        self.files_order: List[str] = dictionary['files_order']
        self.is_public: bool = dictionary['is_public']
        self.is_promoted: bool = dictionary['is_promoted']
        self.is_heroic: bool = dictionary['is_heroic']
        self.updated_at: str = dictionary['updated_at']
        self.deleted_at: Optional[str] = dictionary['deleted_at']
        self.tags: List[Tag] = [Tag(tag) for tag in dictionary['tags']]
        self.files: List[File] = [File(file) for file in dictionary['files']]
        self.user: BasicUser = BasicUser(dictionary['user'])
        self.cover: Optional[str] = dictionary['cover']
        self.is_liked: bool = dictionary['is_liked']
        self.like_count: int = dictionary['like_count']


class Tag:
    def __init__(self, dictionary: dict):
        self.id: int = dictionary['id']
        self.title: str = dictionary['title']
        self.data: Optional[str] = dictionary['data']
        self.created_at: str = dictionary['created_at']
        self.updated_at: str = dictionary['updated_at']


class Hero:
    def __init__(self, dictionary):
        self.id: int = dictionary['id']
        self.thumbnail: str = dictionary['thumbnail'].replace('REMOTE_CURRENT://', _URL)
        self.title: str = dictionary['title']


__all__ = ['Stats', 'Comments', 'Diff', 'User', 'Node', 'Tag', 'Comment', 'BasicUser', 'DiffPost', 'Node']