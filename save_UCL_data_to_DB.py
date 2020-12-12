# Copyright (c) Jakub Wilczyński 2020
from os import listdir
from bs4 import BeautifulSoup
import sqlite3 as lite
import sys


##### CONNECTING TO DATABASE #####
file_db = 'Matches_DB_test.db'
try:
    if path.exists(file_db):
        raise Exception("Impossible connecting to database. The database doesn't exist.")
    conn = lite.connect(file_db)   # database SQLite in the file
    sql = conn.cursor()
except Exception as e:
    print(f"ERROR: {e}")
    exit(-1)

def find_link_and_id(file):
    """ This function finds link to webpage with match centre. """
    with open(f"Matches_Test\\{file}", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        link = soup.find("link", rel="canonical").get("href")
        idx = link.split("/")[4]
        return link, idx

def find_teams(file):
    with open(f"Matches_Test\\{file}", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        teams_names = soup.find("div", id="match-header").find_all("a", class_="team-link")
        teams_ids = soup.find_all("div", class_="pitch-field")
        results = {"team1_name": teams_names[0].string, "team2_name" : teams_names[1].string,
                   "team1_id":teams_ids[0].get("data-team-id"), "team2_id":teams_ids[1].get("data-team-id")}
        return results

def get_paths(file):
    return path.abspath(file)

def find_date(file):
    with open(f"Matches_Test\\{file}", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        match_date = soup.find_all("div", class_="info-block cleared")[2].find_all("dd")[1].string[5:]
        assert len(match_date) == 9
        day, month, year = match_date.split("-")
        match_date = datetime.date(int("20"+year), MONTHS[month], int(day))
        return match_date

"""<div class="info-block cleared"><dl><dt>Kick off:</dt><dd>19:45</dd><dt>Date:</dt><dd>Wed, 15-Sep-10</dd></dl></div>"""
def find_date(file):
    with open(f"Matches_Test\\{file}", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        date = soup.find_all("div", class_="info-block cleared").find("dd").get(string)[5:]
        return date


preview_files = list(filter(lambda x: 'preview' in x, listdir("Matches_Test")))
squad_files = list(filter(lambda x: 'squad' in x, listdir("Matches_Test")))
for file in squad_files:
    print(find_date(file))

