_URL = 'https://pig.vault48.org/'


class Stats:
    def __init__(self, dictionary):
        self.users_total = dictionary['users']['total']
        self.users_alive = dictionary['users']['alive']
        self.nodes_images = dictionary['nodes']['images']
        self.nodes_audios = dictionary['nodes']['audios']
        self.nodes_videos = dictionary['nodes']['videos']
        self.nodes_texts = dictionary['nodes']['texts']
        self.nodes_total = dictionary['nodes']['total']
        self.comments_total = dictionary['comments']['total']
        self.files_count = dictionary['files']['count']
        self.files_size = dictionary['files']['size']
        self.timestamps_boris = dictionary['timestamps']['boris_last_comment']
        self.timestamps_flow = dictionary['timestamps']['flow_last_post']


class Comments:
    def __init__(self, dictionary):
        self.comments = [Comment(comment) for comment in dictionary['comments']]
        self.order = dictionary['order']
        self.comment_count = dictionary['comment_count']


class Diff:
    def __init__(self, dictionary):
        self.before = [DiffPost(post) for post in dictionary['before']]
        self.after = [DiffPost(post) for post in dictionary['after']]
        self.recent = [DiffPost(post) for post in dictionary['recent']]
        self.heroes = [Hero(hero) for hero in dictionary['heroes']]
        # self.updated = dictionary['updated']
        # self.valid = dictionary['valid']


class Comment:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.text = dictionary['text']
        self.files_order = dictionary['files_order']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']
        self.deleted_at = dictionary['deleted_at']
        self.files = [File(file) for file in dictionary['files']]
        self.user = User(dictionary['user'])


class File:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.name = dictionary['name']
        self.orig_name = dictionary['orig_name']
        self.path = dictionary['path']
        self.full_path = dictionary['full_path']
        self.url = dictionary['url'].replace('REMOTE_CURRENT://', _URL)
        self.size = dictionary['size']
        self.type = dictionary['type']
        self.mime = dictionary['mime']
        self.target = dictionary['target']
        self.metadata = dictionary['metadata']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']


class BasicUser:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.photo = File(dictionary['photo'])
        self.username = dictionary['username']


class User(BasicUser):
    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.email = dictionary['email']
        self.role = dictionary['role']
        self.fullname = dictionary['fullname']
        self.description = dictionary['description']
        self.is_activated = dictionary['is_activated']
        self.last_seen = dictionary['last_seen']
        self.last_seen_messages = dictionary['last_seen_messages']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']


class BasicPost:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.title = dictionary['title']
        self.type = dictionary['type']
        self.created_at = dictionary['created_at']
        self.commented_at = dictionary['commented_at']
        self.thumbnail = dictionary['thumbnail'].replace('REMOTE_CURRENT://', _URL) if dictionary['thumbnail'] else None
        self.description = dictionary['description']


class DiffPost(BasicPost):
    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.user = User(dictionary['user'])


class Node(BasicPost):
    def __init__(self, dictionary):
        dictionary = dictionary['node']
        super().__init__(dictionary)
        self.blocks = dictionary['blocks']
        self.files_order = dictionary['files_order']
        self.is_public = dictionary['is_public']
        self.is_promoted = dictionary['is_promoted']
        self.is_heroic = dictionary['is_heroic']
        self.updated_at = dictionary['updated_at']
        self.deleted_at = dictionary['deleted_at']
        self.tags = [Tag(tag) for tag in dictionary['tags']]
        self.files = [File(file) for file in dictionary['files']]
        self.user = BasicUser(dictionary['user'])
        self.cover = dictionary['cover']
        self.is_liked = dictionary['is_liked']
        self.like_count = dictionary['like_count']


class Tag:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.title = dictionary['title']
        self.data = dictionary['data']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']


class Hero:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.thumbnail = dictionary['thumbnail'].replace('REMOTE_CURRENT://', _URL)
        self.title = dictionary['title']


__all__ = ['Stats', 'Comments', 'Diff', 'User', 'Node', 'Tag', 'Comment', 'BasicUser', 'DiffPost', 'Node']