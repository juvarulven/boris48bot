class Comments:
    def __init__(self, dictionary):
        self.comments = dictionary['comments']
        self.order = dictionary['order']
        self.comment_count = dictionary['comment_count']


class Comment:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.text = dictionary['text']
        self.files_order = dictionary['files_order']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']
        self.deleted_at = dictionary['deleted_at']


class File:
    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.name = dictionary['name']
        self.orig_name = dictionary['orig_name']
        self.path = dictionary['path']
        self.full_path = dictionary['full_path']
        self.url = dictionary['url']
        self.size = dictionary['size']
        self.type = dictionary['type']
        self.mime = dictionary['mime']
        self.target = dictionary['target']
        self.metadata = dictionary['metadata']
        self.created_at = dictionary['created_at']
        self.updated_at = dictionary['updated_at']
