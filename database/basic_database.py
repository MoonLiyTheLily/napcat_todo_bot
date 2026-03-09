import sqlite3
from pathlib import Path
from enum import Enum
from typing import Dict


class BasicDatabase:

    def __init__(self, table_name: str) -> None:
        self.table_name: str = table_name
        self.columns: Dict[str, str] = {}

    def initialize(self, columns: Dict[str, str]):
        if len(columns) == 0:
            return
        sql_command = f"CREATE TABLE IF NOT EXISTS {self.table_name}("
        columns_list = []
        for name, data_type in columns.items():
            columns_list.append(f"{name} {data_type}")

        sql_command += ",".join(columns_list) + ")"
        print(sql_command)

    def add(self, values: list):
        pass

    def check(self, check_value):
        pass

    def update(self):
        pass

    def delete(self):
        pass


if __name__ == "__main__":
    b = BasicDatabase("afj")
    d = {"ID": "INTEGER PRIMARY KEY", "LISJ": "TEXT NOT NULL"}
    b.initialize(d)
