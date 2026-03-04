import sqlite3
import logging
from pathlib import Path


class BasicDatabase:
    def __init__(self, table_name: str) -> None:
        self.table_name: str = table_name

    def initialize(self):
        pass

    def add(self, values):
        pass

    def check(self, check_value):
        pass

    def update(self):
        pass

    def delete(self):
        pass
