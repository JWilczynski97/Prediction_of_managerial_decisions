# Copyright (c) Jakub Wilczyński 2020
# The task of this program is saving the data about UEFA Champions League matches into the database SQLite.
# These data include in the html files in the directory "Matches" on the local disk. The script saves into the
# local database into table "UCL_Matches" these informations about the UCL matches: index, team home, team away, season,
# hoScored id of match, date, path to file with "Centre", path to file with "Preview", link to the website with "Centre".
# Data about teams are saved into table "Team": Whoscored id of team, team name, league (country), link to webpage.
# Tools used: Python 3.8, BeautifulSoup  4.9.1, SQLite 3.28.0

from tools import Database, Logger
from os import listdir, path
from bs4 import BeautifulSoup
import logging
import sqlite3 as lite
from sys import exit
import datetime

###### important structures ######
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015',
               '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
MATCHES_FOLDER = 'Matches'
DATABASE = 'Matches_DB.db'


##### functions #####
def matches_indexes(ucl_season: str) -> [int]:
    """This function returns indexes of matches from given season.\n
        :param ucl_season: str, name of UEFA Champions League season"""
    squads_files = list(filter(lambda x: 'squad' in x, listdir(f"Matches\\{ucl_season.replace('/', '_')}")))
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


def get_teams(html_file: str) -> {str}:
    """This function returns WhoScored IDs, names and leagues of both teams in shape of dictionary.
    Keys of the resulting dictionary: 'team1_name', 'team2_name', 'team1_id', 'team2_id',
    'team1_league', 'team2_league'. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        teams_names = soup.find("div", id="match-header").find_all("a", class_="team-link")
        teams_ids = soup.find_all("div", class_="pitch-field")
        results = {"team1_name": teams_names[0].string, "team2_name": teams_names[1].string,
                   "team1_id": teams_ids[0].get("data-team-id"), "team2_id": teams_ids[1].get("data-team-id"),
                   "team1_league": teams_names[0].get("href").split("/")[-1].split("-")[0],
                   "team2_league": teams_names[1].get("href").split("/")[-1].split("-")[0]}
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


def get_season(html_file: str) -> str:
    """This function returns name of UCL season for the given match. \n
        :param html_file: str, path to the file with match centre"""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        this_season = soup.find("title").string.strip().split(" ")[-2]
        return this_season


def change_team_name(team_id, team_name):
    """This function changes tha names of few clubs.
    The correct names are very importent for the next step of project.\n
    :param team_id: str, WhoScored id of team
    :param team_name: str, WhoScored id of team"""
    change_names = {'32': 'Manchester United', '167': 'Manchester City', '7614': 'Leipzig',
                    '134': 'Borussia M Gladbach',
                    '296': 'Sporting CP', '560': 'Zenit St Petersburg', '304': 'Paris Saint Germain'}
    if team_id in change_names:
        return change_names[team_id]
    return team_name

##### Script #####
logger = Logger(log_folder=None, std_output=True)
db = Database(DATABASE, logger)
try:
    for season in ALL_SEASONS:
        for idx in matches_indexes(season):  # for every saved UCL match

            ### downloading data from html files ###
            file = f"{MATCHES_FOLDER}/{season.replace('/', '_')}/Match_{idx}_squad.html"
            link, whoscored_id = get_link_and_id(file)
            paths = get_paths(file)
            match_date = get_date(file)
            teams = get_teams(file)
            teams["team1_name"] = change_team_name(teams["team1_id"], teams["team1_name"])
            teams["team2_name"] = change_team_name(teams["team2_id"], teams["team2_name"])
            season = get_season(file)
            link_team_1 = f"whoscored.com/Teams/{teams['team1_id']}"
            link_team_2 = f"whoscored.com/Teams/{teams['team2_id']}"

            ### adding UCL match to the database ###
            row = (idx, teams["team1_id"], teams["team2_id"], season, whoscored_id, match_date, paths[0], paths[1], link)
            logger.write(f"Data downloaded from file {file}.")
            db.insert('UCL_Matches', False, *row)
            logger.write(f"Match with ID {whoscored_id} saved in the database.")

            ### adding team to the database if not exists ###te
            if not db.is_element_in_db("Teams", Team_ID=teams["team1_id"]):
                db.insert('Teams', False, teams["team1_id"], teams["team1_name"], teams["team1_league"], link_team_1)
                logger.write(f"Team with ID {teams['team1_id']} saved in the database.")

            if not db.is_element_in_db("Teams", Team_ID=teams["team2_id"]):
                db.insert('Teams', False, teams["team2_id"], teams["team2_name"], teams["team2_league"], link_team_2)
                logger.write(f"Team with ID {teams['team2_id']} saved in the database.")

            db.commit()
            logger.write(f"Changes in the database {DATABASE} saved.")
            logger.write(f"File {file} complete.")
except lite.Error as e:
    if db:
        db.rollback()
    logger.write(f"SQLite ERROR: {e}", level=logging.ERROR)
except Exception as e:
    if db:
        db.rollback()
    logger.write(f"ERROR: {e}")
else:
    db.commit()
    logger.write(f"All changes in the database {DATABASE} saved.")
