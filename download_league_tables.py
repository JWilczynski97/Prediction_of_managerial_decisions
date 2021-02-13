# Copyright (c) Jakub Wilczyński 2020

from tools import Database, Logger

from os import path, rename
import datetime
from itertools import product
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from random import uniform

###### WEBDRIVER OPTIONS #####
OPTIONS = Options()
OPTIONS.add_argument('start-maximized')  # maximize of the browser window
OPTIONS.add_experimental_option("excludeSwitches",
                                ['enable-automation'])  # process without information about the automatic test
OPTIONS.add_argument("chrome.switches")
OPTIONS.add_argument("--disable-extensions")
DRIVER_PATH = 'Chromedriver\chromedriver.exe'  # path to the webdriver file

ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015', '2015/2016', '2016/2017', '2017/2018',
               '2018/2019', '2019/2020']
LEAGUES = {"England": 'English Premier', "France": 'French Le Championnat', "Italy": 'Italian Serie A',
           "Germany": 'German Bundesliga 1', "Spain": 'Spanish La Liga 1', "Turkey": 'Turkish Ligi 1',
           "Portugal": 'Portugal Liga I', "Netherlands": 'Dutch KPN Eredivisie', "Russia": None}
NUM_WEEKS = {"England": 38, "France": 20, "Italy": 38, "Germany": 34, "Spain": 38, "Turkey": 34,
             "Portugal": 34, "Netherlands": 34, "Russia": 30}
NUM_TEAMS = {"England": 20, "France": 20, "Italy": 20, "Germany": 18, "Spain": 20, "Turkey": 18,
             "Portugal": 18, "Netherlands": 18, "Russia": 16}
FOLDER = "League_tables"

##### functions #####
def wait(x, y):
    """This function launches sleep function for a few seconds. Number of seconds is a random floating point number x to y.\n
    :param x: int, start of interval
    :param y: int, end of interval"""
    sleep(uniform(x, y))

def is_element_clickable(element):
    """If the element isn't clickable, the current page waits one time or raises Exception..\n
    :param element: Element, the element from the current page"""
    if not element_to_be_clickable(element):
        log.write("The element is not yet clickable. Waiting...")
        wait(8, 10)
    if not element_to_be_clickable(element):
        log.write("Unexpected error! The element is not clickable.")
        raise Exception("Unexpected error! The element is not clickable.")

def save_file(html_code, name_file):
    """This function saves the html code of webpage to the file.\n
    :param html_code: str, contains html code of current downloaded website;
    :param name_file: str, name of saving file.
    """
    global league, season
    with open(name_file, 'w', encoding="utf-8") as f:
        f.write(str(html_code))
        log.write(
            f"The website with table of league from {league} in the season {season} downloaded and saved into file {f.name}.")


def select_competitions(country, edition, this_date):
    league_menu, season_menu = browser.find_element_by_name("league"), browser.find_element_by_name("season")
    select_league = Select(league_menu)
    is_element_clickable(league_menu)
    select_league.select_by_visible_text(LEAGUES[country])
    wait(1.5, 2.5)
    select_season = Select(season_menu)
    is_element_clickable(season_menu)
    select_season.select_by_visible_text(edition)
    wait(1.5, 2.5)
    input_date = browser.find_element_by_id("thisdate")
    input_date.clear()
    this_date = generate_date_for_footstats(this_date)
    input_date.send_keys(this_date)
    browser.find_element_by_xpath('//*[@id="site-wrapper"]/div[3]/form/div/div[4]/input').click()

def check_league_and_season(ucl_season, league_name):
    """Preview section on whoscored.com is available only for few leagues and correct seasons.
    This function checks this condition and returns answer True/False. \n
    :param ucl_season: str, name of checked season
    :param league_name: str, name of checked league"""
    if league_name in ['England', 'Spain', 'Germany', 'Italy',
                       'France']:  # TOP 5 leagues - all seasons with available Preview section
        return True
    if league_name in ['Netherlands', 'Russia'] and ucl_season in ALL_SEASONS[3:]:  # NED and RUS - from 2013/2014
        return True
    if league_name == 'Turkey' and ucl_season in ALL_SEASONS[4:]:  # Turkey - from 2014/2015
        return True
    if league_name == 'Portugal' and ucl_season in ALL_SEASONS[-4:]:  # Portugal - from 2016/2017
        return True
    return False


def create_table(db, table_name):
    db.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (
	"Position"	INTEGER NOT NULL,
	"Team_name"	TEXT,
	"Team_ID"	INTEGER NOT NULL,
	"Matches"	INTEGER,
	"Wins"	INTEGER,
	"Draws"	INTEGER,
	"Loses"	INTEGER,
	"Scored"	INTEGER,
	"Conceded"	INTEGER,
	"Points"	INTEGER)''')
    log.write(f"Table {table_name} created in the database {db.name}.")
    db.commit()


def download_russia_websites(seas):
    for week in list(range(1, 24)):
        html_file = f"{FOLDER}\\{seas.replace('/', '_')}\\Russia\\Russia_{seas.replace('/', '_')}_week_{str(week)}.html"
        if path.exists(html_file):
            log.write(f"File {html_file} is already downloaded. Skip!")
            continue
        # downloading websites and saving into html files
        link = generate_link(seas, week)
        log.write(f"Launching the website in address {link}...")
        browser.get(link)
        wait(2, 3)
        if week == 1:
            browser.find_element_by_xpath('/html/body/div[4]/div[2]/div[1]/div[2]/div[2]/button[1]/p').click()
            log.write("Cookies button on worldfootball.net clicked.")
            wait(3, 5)
        save_file(browser.page_source, html_file)


def save_russia_data_into_db(db, sea):
    for w in list(range(1, 24)):
        with open(f"League_tables\\{sea.replace('/', '_')}\\Russia_{sea.replace('/', '_')}_week_{w}", "r",
                  encoding="UTF-8") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            table_matches = soup.find_all("table", class_="standard_tabelle")[0].find("tbody")
            term = [element.find("td").string for element in table_matches.find_all("tr")][0]
            assert len(term) == 10
            day, month, year = term.split("/")
            day = f"{year}-{month}-{day}"
            table = f"Russia_{sea.replace('/', '_')}_day_{day.replace('-','_')}"
            create_table(db, table)
            table_league = soup.find_all("table", class_="standard_tabelle")[1].find("tbody")
            rows = table_league.find_all("tr")[1:]
            assert len(rows) == 10
            for row in rows:
                data = row.find_all("td")
                position = rows.index(row) + 1
                name = data[2].find("a")['title']
                games = [int(num.string) for num in data[3:7]]
                scored, conceded = data[7].string.split(":")
                db.insert(table, True, position, name, 0, games[0], games[1], games[2],
                          games[3], scored, conceded, data[8].string)
            log.write(f"The data about league table in Russia in the season {sea} and week {w} saved into the db.")


def generate_link(s, w):
    return f'https://www.worldfootball.net/schedule/rus-premier-liga-{s.replace("/", "-")}-spieltag/{str(w)}/'


def generate_date_for_footstats(match_date: str):
    year, month, day = match_date.split("-")
    new_date = str(datetime.date(int(year), int(month), int(day)) - datetime.timedelta(days=1))
    year, month, day = new_date.split("-")
    return f"{day}/{month}/{year}"


def download_websites(select_season, select_league):
    for match in database.select("Matches", order_by="Date", Season=select_season, League=select_league):
        date = match['Date']
        year, month, day = date.split("-")
        new_date = str(datetime.date(int(year), int(month), int(day)) - datetime.timedelta(days=1))
        file = f"{FOLDER}\\{select_season.replace('/', '_')}\\{select_league}\\{select_league}_{select_season.replace('/', '_')}_day_{new_date}.html"
        if path.exists(file):
            log.write(f"File {file} is already downloaded. Skip!")
            continue
        if browser.current_url != "http://www.footstats.co.uk/index.cfm?task=league_full":
            browser.get('http://www.footstats.co.uk/index.cfm?task=league_full')
            wait(2, 3)
        select_competitions(select_league, select_season, date)
        wait(3, 4)
        save_file(browser.page_source, file)


def save_data_into_db(db, edition, competition):
    for match in database.select("Matches", order_by="Date", Season=edition, League=competition):
        year, month, day = match['Date'].split("-")
        new_date = str(datetime.date(int(year), int(month), int(day)) - datetime.timedelta(days=1))
        html = f"{FOLDER}\\{edition.replace('/', '_')}\\{competition}\\{competition}_{edition.replace('/', '_')}_day_{new_date}.html"
        table = f"{competition}_{edition.replace('/', '_')}_day_{new_date.replace('-', '_')}"
        create_table(db, table)
        if len(db.select(table)) > 10:
            continue
        with open(html, "r", encoding="UTF-8") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.find("div", class_='alert alert-danger') is not None:
                log.write(f"Day: {new_date}. Status before first week of season {edition} in {competition}. Empty table saved into the database.")
                for _ in range(0, NUM_TEAMS[competition]):  # no data about teams with 0 played matches
                    db.insert(table, True, 0, '', 0, 0, 0, 0, 0, 0, 0, 0)
                continue
            tbody = soup.find("table", attrs={"id": "sleague"}).find("tbody")
            rows = tbody.find_all("tr")
            for row in rows:
                data = [element.string for element in row.find_all("td")]
                db.insert(table, True, data[0], data[1], 0, data[2], data[3], data[4], data[5], data[6], data[7], data[9])
        if len(db.select(table)) < NUM_TEAMS[competition]:  # Warning: in a few tables can be missing data (no names of teams with 0 matches).
            for _ in range(0, NUM_TEAMS[competition] - len(db.select(table))):
                db.insert(table, True, 0, '', 0, 0, 0, 0, 0, 0, 0, 0)
        log.write(f"The data about league table in {competition} in the season {edition} from day {new_date} saved into the db.")


##### Script #####
browser = webdriver.Chrome(executable_path=DRIVER_PATH, options=OPTIONS)
log = Logger(std_output=True)
db_tables = Database("League_Tables.db", logger=log)
database = Database("Matches_DB_copy.db", logger=log)

for season, league in product(ALL_SEASONS, list(LEAGUES.keys()) + ["Russia"]):
    if not check_league_and_season(season, league):
        continue
    log.write(f"Season: {season}. League: {league}")
    if league == "Russia":
        # download websites with league tables in Russia from worldfootball.net
        download_russia_websites(season)
        # saving data into database League_Matches.db
        save_russia_data_into_db(db_tables, season)
        continue
    # download websites with league tables from ww.footstats.co.uk/
    download_websites(season, league)
    # saving data into database League_Matches.db
    save_data_into_db(db_tables, season, league)

log.write("THE END. All websites with league tables downloaded.")
