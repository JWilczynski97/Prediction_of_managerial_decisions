# Copyright (c) Jakub Wilczyński 2020
# Module with helpful classes in the project.
# classes: Database, Logger

import sqlite3 as lite
import logging
import datetime
import sys
from typing import Dict

from unidecode import unidecode
from os import listdir, path
from time import asctime, localtime


class Database:
    """Class to represent the SQLite database in 'file'."""

    def __init__(self, file, logger=None, by_column=True):
        """ Function to create connection to the database and cursor. \n
        :param path: str, path to .db file with sqlite database
        :param logger: Logger, object of class Logger (not necessary)"""
        self.logger = logger
        if not path.exists(file):
            self.log(f"Connection SQLite ERROR: impossible connecting to database."
                     f"The file {file} doesn't exist.", level=logging.ERROR)
            sys.exit(1)
        self.name = file
        self.connection = lite.connect(self.name)       # Connection object
        if by_column:
            self.connection.row_factory = lite.Row          # to access values by column name
        self.cursor = self.connection.cursor()
        self.log(f"Connected to the database {self.name}.")

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def connect(self, by_column=True):
        """Method to create the connection to the database and cursor object.
        :param by_column: to access values by column name (if True)"""
        self.connection = lite.connect(self.name)       # Connection object
        if by_column:
            self.connection.row_factory = lite.Row
        self.cursor = self.connection.cursor()          # Cursor object

    def disconnect(self):
        """Method to close the connection to the database."""
        self.cursor.close()
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
        self.log(f"{self.name}: table {table} -> new row added: {args}")
        if commit is True:
            self.commit()

    def update(self, table, column, value, commit=True, **condition):
        self.cursor.execute(f"""UPDATE {table} SET '{column}' = '{value}' WHERE "{condition}" = ?""", (*condition.values(),))
        if commit is True:
            self.commit()

    def select(self, table, order_by='', option_order='',
               **conditions):  # (SELECT * FROM <table> WHERE column_1=value_1 AND column_2=value_2 ORDER BY <column>)
        """Method to execute SELECT statement in the database with given conditions.\n
        :param table: str, name of table
        :param order_by: str, data are sorted by this column name
        :param option_order: str, default = ASC (ascending), other: DESC (descending)
        :param conditions: tuple, <column_name>=<value> conditions"""
        where = f" WHERE {' AND '.join([f'{condition}=?' for condition in conditions])}" if len(conditions) != 0 else ''
        order = f' ORDER BY {order_by} {option_order}' if order_by != '' != "ASC" else ''
        assert option_order in ('', 'ASC', 'DESC')
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
        return len(self.select(table, **conditions)) > 0
 

class Logger:
    """Object to log text using the logging module.
    The messages can be wrote to the standard output and saved to the files on the local disk in directory log_folder."""

    def __init__(self, log_folder=None, std_output=False):
        self.log_folder = log_folder
        self.std_output = std_output
        if log_folder:
            num, now = len(listdir(log_folder)) + 1, datetime.datetime.now()
            logging.basicConfig(handlers=[logging.FileHandler(f'{log_folder}\\{now.date()}_Log_{num}.txt', 'w', "utf8")],
                                format=f'%(asctime)s - %(levelname)s - %(message)s', level="NOTSET")
            self.log = logging.getLogger('')
            self.write("Logger created.")

    def write(self, message, level=logging.INFO):
        try:
            if self.log_folder:
                self.log.log(level, message)
            if self.std_output is True:
                print(f'{asctime(localtime())} - {logging.getLevelName(level)} - {message}')
        except UnicodeEncodeError:
            self.write(unidecode(message), level)
