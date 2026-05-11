import sqlite3
from pathlib import Path
from enum import Enum
from typing import Any


class BasicDatabase:

    def __init__(self, table_name: str) -> None:
        self.table_name: str = table_name
        self.columns: dict[str, str] = {}

    def initialize(self, columns: dict[str, str]) -> None:
        if len(columns) == 0:
            return
        sql_command = f"CREATE TABLE IF NOT EXISTS {self.table_name}("
        columns_list = []
        for name, data_type in columns.items():
            columns_list.append(f"{name} {data_type}")

        sql_command += ",".join(columns_list) + ")"
        print(sql_command)

    def add(self, values: list[Any]) -> None:
        pass

    def check(self, check_value: Any) -> None:
        pass

    def update(self) -> None:
        pass

    def delete(self) -> None:
        pass


if __name__ == "__main__":
    b = BasicDatabase("afj")
    d = {"ID": "INTEGER PRIMARY KEY", "LISJ": "TEXT NOT NULL"}
    b.initialize(d)
