import bson
import os


class Database:
    save_lock = False

    def __init__(self, filename):
        self._filename = filename
