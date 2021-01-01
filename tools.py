# Copyright (c) Jakub Wilczyński 2020
# Module with helpful classes in the project.
# classes: Database, Logger

import sqlite3 as lite
import logging
import datetime
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
        self.connection = lite.connect(self.name)
        self.connection.row_factory = lite.Row
        self.cursor = self.connection.cursor()
        self.log(f"Connected to the database {self.name}.")

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def __del__(self):
        """Method to close the connection to the database."""
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

    def select(self, table, order_by='',
               **conditions):  # (SELECT * FROM <table> WHERE column_1=value_1 AND column_2=value_2 ORDER BY <column>)
        """Method to execute SELECT statement in the database with given conditions.\n
        :param table: str, name of table
        :param order_by: str, data are sorted by this column name
        :param conditions: tuple, <column_name>=<value> conditions"""
        where = f" WHERE {' AND '.join([f'{condition}=?' for condition in conditions])}" if len(conditions) != 0 else ''
        order = f' ORDER BY {order_by}' if order_by != '' else ''
        rows = self.cursor.execute(f"SELECT * FROM {table}" + where + order, (*conditions.values(),))
        return rows.fetchall()

    def is_element_in_db(self, table, **conditions):
        """The method to check the given element is already in the database.\n
        :param table: str, name of table in the database
        :param conditions: tuple, <column_name>=<value> conditions"""
        found = self.select(table, **conditions)
        answer = False if len(found) == 0 else True
        return answer


class Logger:
    """Object to log text using the `logging` module.
    The messages can be printed in the standard output and saved to the files on the local disk in directory log_folder."""
    def __init__(self, log_folder=None, std_output=False):
        self.log_folder = log_folder
        if log_folder:
            num, now = len(listdir(log_folder)) + 1, datetime.datetime.now()
            logging.basicConfig(filename=f'{log_folder}\\{now.date()}_Log_{num}.txt',
                                filemode='w', format=f'%(asctime)s - %(levelname)s - %(message)s', level="NOTSET")
            self.log = logging.getLogger('')
            self.write("Logger created.")
        self.std_output = std_output

    def write(self, message, level=logging.INFO):
        if self.log_folder:
            self.log.log(level, message)
        if self.std_output is True:
            print(f'{asctime(localtime())} - {logging.getLevelName(level)} - {message}')
