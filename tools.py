# Copyright (c) Jakub Wilczyński 2020
# Module with helpful classes in the project.
# classes: Database, Logger

import sqlite3 as lite
import logging
import datetime
import sys
from os import listdir, path
from time import asctime, localtime


class Database:
    """Object to represent the SQLite database in 'file'."""

    def __init__(self, file, logger=None):
        """ Function to create connection to the database and cursor. \n
        :param path: str, path to .db file with sqlite database
        :param logger: Logger, object of class Logger (not necessary)"""
        self.logger = logger
        if not path.exists(file):
            self.log(f"Connection SQLite ERROR: impossible connecting to database."
                     f"The file {file} doesn't exist.", level=logging.ERROR)
            sys.exit(1)
        self.name = file
        self.connection = lite.connect(self.name)  # Connection object
        self.connection.row_factory = lite.Row  # to access valeus by column name
        self.cursor = self.connection.cursor()  # Cursor object
        self.log(f"Connected to the database {self.name}.")

    def __enter__(self):
            return self

    def __exit__(self, ext_type, exc_value, traceback):
            self.cursor.close()
            if isinstance(exc_value, Exception):
                self.rollback()
            else:
                self.commit()
            self.close()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def __del__(self):
        """Method to close the connection to the database."""
        self.cursor.close()
        self.connection.close()
        self.log(f"Disconnected from the database {self.name}.")

    def log(self, message, level=logging.INFO):
        """Method to write logs (if logger is defined)."""
        if self.logger:
            self.logger.write(message, level=level)

    def insert(self, table, commit=True, *args):  # (INSERT INTO <table> VALUES(?,?,?,?), <values>)
        """Method to add new row of data into the given table into the database.\n
        :param table: name of table in the database
        :param commit: bool, changes in database are commited if it is True
        :param args: tuple, <column_name>=<value> conditions"""
        self.cursor.execute(f"INSERT INTO {table} VALUES({','.join(['?' for _ in args])})", (*args,))
        self.log(f"table {table} -> new row added: {args}")
        if commit is True:
            self.commit()

    def update(self, table, column, value, **condition):
        self.cursor.execute(f"UPDATE {table} SET {column} = {value} WHERE {condition} = ?", (*condition.values(),))
        self.commit()

    def many_columns_update(self, table, column, condition, **values):
        query_set = f" SET {' AND '.join([f'{value}=?' for value in values])}" if len(values) != 0 else ''
        self.cursor.execute(f"UPDATE {table} {query_set} WHERE {column} = {condition}", (*values.values(),))
        self.commit()

    def select(self, table, order_by='', option_order='',
               **conditions):  # (SELECT * FROM <table> WHERE column_1=value_1 AND column_2=value_2 ORDER BY <column>)
        """Method to execute SELECT statement in the database with given conditions.\n
        :param table: str, name of table
        :param order_by: str, data are sorted by this column name
        :param option_order: str, default = ASC (ascending), other: DESC (descending)
        :param conditions: tuple, <column_name>=<value> conditions"""
        where = f" WHERE {' AND '.join([f'{condition}=?' for condition in conditions])}" if len(conditions) != 0 else ''
        order = f' ORDER BY {order_by} {option_order}' if order_by != ''!= "ASC" else ''
        if option_order not in ('', 'ASC', 'DESC'):
            raise Exception("Error! Incorrect option of ordering.")
        rows = self.cursor.execute(f"SELECT * FROM {table}" + where + order, (*conditions.values(),))
        return rows.fetchall()

    def create_table(self, table_name, *columns):
        self.cursor.execute(f"CREATE TABLE if not exists {table_name} ({','.join(['?' for _ in columns])})",
                            (*columns,))
        self.commit()

    def is_element_in_db(self, table, **conditions):
        """The method to check the given element is already in the database.\n
        :param table: str, name of table in the database
        :param conditions: tuple, <column_name>=<value> conditions"""
        found = self.select(table, **conditions)
        answer = False if len(found) == 0 else True
        return answer


class Logger:
    """Object to log text using the `logging` module.
    The messages can be wrote to the standard output and saved to the files on the local disk in directory log_folder."""

    def __init__(self, log_folder=None, std_output=False):
        self.log_folder = log_folder
        self.std_output = std_output
        if log_folder:
            num, now = len(listdir(log_folder)) + 1, datetime.datetime.now()
            logging.basicConfig(filename=f'{log_folder}\\{now.date()}_Log_{num}.txt',
                                filemode='w', format=f'%(asctime)s - %(levelname)s - %(message)s', level="NOTSET")
            self.log = logging.getLogger('')
            self.write("Logger created.")

    def write(self, message, level=logging.INFO):
        if self.log_folder:
            self.log.log(level, message)
        if self.std_output is True:
            print(f'{asctime(localtime())} - {logging.getLevelName(level)} - {message}')

print("Module tools.py imported.")