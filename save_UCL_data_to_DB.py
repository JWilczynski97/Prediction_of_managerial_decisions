# Copyright (c) Jakub Wilczyński 2020
from os import listdir, path
from bs4 import BeautifulSoup
import sqlite3 as lite
from sys import exit
import datetime

###### important structures ######
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015',
               '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
database = 'Matches_DB.db'


##### functions #####
def matches_indexes(ucl_season: str) -> List[int]:
    """This function returns indexes of matches from given season.\n
        :param ucl_season: str, name of UEFA Champions League season"""
    squads_files = list(filter(lambda x: 'squad' in x, listdir(f"Matches\\{ucl_season.replace('/','_')}")))
    ids = [int(x.split("_")[1]) for x in squads_files]
    return sorted(ids)


def get_link_and_id(html_file: str) -> (str, str):
    """ This function returns link to webpage with match centre and WhoScored ID of the given match
        in form od two-element tuple. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        whoscored_link = soup.find("link", rel="canonical").get("href")
        match_id = whoscored_link.split("/")[4]
        return whoscored_link, match_id


def get_teams(html_file: str) -> Dict[str, str]:
    """This function returns WhoScored IDs and names of both teams in shape of dictionary.
    Keys of the resulting dictionary: 'team1_name', 'team2_name', 'team1_id', 'team2_id'. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        teams_names = soup.find("div", id="match-header").find_all("a", class_="team-link")
        teams_ids = soup.find_all("div", class_="pitch-field")
        results = {"team1_name": teams_names[0].string, "team2_name": teams_names[1].string,
                   "team1_id": teams_ids[0].get("data-team-id"), "team2_id": teams_ids[1].get("data-team-id")}
        return results


def get_paths(html_file: str) -> (str, str):
    """ This function returns paths to the match centre and preview files for given match. \n
        :param html_file: str, path to the file with match centre"""
    return path.relpath(html_file), path.relpath(html_file.replace("squad", "preview"))


def get_date(html_file: str) -> str:
    """This function returns date of match in the format yyyy-mm-dd. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        game_date = soup.find_all("div", class_="info-block cleared")[2].find_all("dd")[1].string[5:]
        assert len(game_date) == 9
        day, month, year = game_date.split("-")
        game_date = datetime.date(int("20" + year), MONTHS[month], int(day))
        return str(game_date)


def get_season(html_file):
    """This function returns name of UCL season for the given match. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        this_season = soup.find("title").string.strip().split(" ")[-2]
        return this_season


def connection_to_db(file_db):
    """This function connects program with SQLite database and returns connection object. \n
    :param file_db: str, path to the .db file with database"""
    if not path.exists(file_db):
        print(f"{datetime.datetime.now()}          Connection ERROR: impossible connecting to database. The file {file_db} doesn't exist.")
        sys.exit(1)
    connection = lite.connect(file_db)
    print(f"{datetime.datetime.now()}          Connected to the database {file_db}")
    return connection


def is_element_in_db(cursor, element, table, column):
    """This function checks the given element is already in the database.
    Then it returns answer in bool object: True or False. \n
    :param cursor: cursor object, cursor using in the connection with the database
    :param element: str, element whose presence in the database is checked
    :param table: str, name of correct table in the database
    :param column: str, name of correct column in the database"""
    cursor.execute(f"SELECT * FROM {table} WHERE {column}= ?", (element,))
    found = cursor.fetchall()   # it returns a list of rows (tuples)
    result = True if len(found) != 0 else False
    return result

##### Script #####
conn = None
try:
    conn = connection_to_db(database)
    sql = conn.cursor()
    for season in ALL_SEASONS:
        for idx in matches_indexes(season):       # for every saved UCL match

            ### downloading data from html files ###
            file = f"Matches/{season.replace('/', '_')}/Match_{idx}_squad.html"
            link, whoscored_id = get_link_and_id(file)
            paths = get_paths(file)
            match_date = get_date(file)
            teams = get_teams(file)
            season = get_season(file)

            ### adding UCL match to the database ###
            row = (idx, teams["team1_id"], teams["team2_id"], season, whoscored_id, match_date, paths[0], paths[1], link)
            print(f"{datetime.datetime.now()}          Data downloaded from file {file}.")
            sql.execute("INSERT INTO UCL_Matches VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
            print(f"{datetime.datetime.now()}          Match with ID {whoscored_id} saved in the database.")

            ### adding team to the database if not exists ###
            if not is_element_in_db(sql, teams["team1_id"], "Teams", "Team_ID"):
                sql.execute("INSERT INTO Teams VALUES(?, ?)", (teams["team1_id"], teams["team1_name"]))
                print(f"{datetime.datetime.now()}          Team with ID {teams['team1_id']} saved in the database.")
            if not is_element_in_db(sql, teams["team2_id"], "Teams", "Team_ID"):
                sql.execute("INSERT INTO Teams VALUES(?, ?)", (teams["team2_id"], teams["team2_name"]))
                print(f"{datetime.datetime.now()}          Team with ID {teams['team2_id']} saved in the database.")
            conn.commit()
            print(f"{datetime.datetime.now()}          Changes in the database {database} saved.")
            print(f"{datetime.datetime.now()}          File {file} complete.")
except lite.Error as e:
    if conn:
        conn.rollback()
    print(f"{datetime.datetime.now()}          SQLite ERROR: {e}")
except Exception as e:
    if conn:
        conn.rollback()
    print(f"{datetime.datetime.now()}          ERROR: {e}")
else:
    conn.commit()
    print(f"{datetime.datetime.now()}          All changes in the database {database} saved.")
finally:
    if conn:
        conn.close()
    print(f"{datetime.datetime.now()}          Disconnected from the database {database}.")