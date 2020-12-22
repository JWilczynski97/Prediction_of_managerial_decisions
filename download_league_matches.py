from os import listdir, path, getcwd, makedirs
import logging
import datetime
from sys import stdout
import csv
import sqlite3 as lite
from time import asctime, localtime, sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from random import uniform
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
import pandas as pd

###### WEB DRIVER OPTIONS #####
options = Options()
options.add_argument('start-maximized')  # maximize of the browser window
options.add_experimental_option("excludeSwitches",
                                ['enable-automation'])  # process without information about the automatic test
options.add_argument("chrome.switches")
options.add_argument("--disable-extensions")
# browser = webdriver.Chrome(executable_path='Chromedriver\chromedriver.exe', options=options)

##### important structures ####
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015',
               '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
LEAGUES = {'England': 'https://www.whoscored.com/Regions/252/Tournaments/2/',
           'Spain': 'https://www.whoscored.com/Regions/206/Tournaments/4/,',
           'Germany': 'https://www.whoscored.com/Regions/81/Tournaments/3/,',
           'France': 'https://www.whoscored.com/Regions/74/Tournaments/22/',
           'Italy': 'https://www.whoscored.com/Regions/108/Tournaments/5/',
           'Russia': 'https://www.whoscored.com/Regions/182/Tournaments/77/',
           'Netherlands': 'https://www.whoscored.com/Regions/155/Tournaments/13/',
           'Turkey': 'https://www.whoscored.com/Regions/225/Tournaments/17/',
           'Portugal': 'https://www.whoscored.com/Regions/177/Tournaments/21/',
           'Scotland': 'https://www.whoscored.com/Regions/253/Tournaments/20/'}
MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
LOGS_FOLDER = 'Logs_test'
LINKS_FOLDER = 'Links'
DATABASE = 'Matches_DB_copy.db'


class Logger:
    """File-like object to log text using the `logging` module."""

    def __init__(self, folder):
        num, now = len(listdir(folder)) + 1, datetime.datetime.now()
        logging.basicConfig(filename=f'{folder}\\{now.date()}_Log_{num}.txt',
                            filemode='w', format=f'%(asctime)s - %(levelname)s - %(message)s', level="NOTSET")
        self.log = logging.getLogger('')
        self.write("Logger created.")

    def write(self, message, level=logging.INFO):
        levels = {0: "NOTSET", 10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
        self.log.log(level, message)
        print(f'{asctime(localtime())} - {levels[level]} - {message}')


class Database:
    def __init__(self, database_name):
        if not path.exists(database_name):
            log.write(f"Connection SQLite ERROR: impossible connecting to database. "
                      f"The file {database_name} doesn't exist.", level=logging.ERROR)
            sys.exit(1)
        self.connection = lite.connect(database_name)
        self.connection.row_factory = lite.Row
        self.cursor = self.connection.cursor()
        log.write(f"Connected to the database {database_name}.")

    def __del__(self):
        self.connection.close()

    def insert(self, table, *args):
        self.cursor.execute(f"INSERT INTO {table} VALUES({','.join(['?' for _ in args])})", (args,))
        self.connection.commit()

    def select(self, table, order_by='', **conditions):
        where = f" WHERE {' AND '.join([f'{condition}=?' for condition in conditions])}" if len(conditions) != 0 else ''
        order = f' ORDER BY {order_by}' if order_by != '' else ''
        rows = self.cursor.execute(f"SELECT * FROM {table}" + where + order, (*conditions.values(),))
        return rows.fetchall()

    def is_element_in_db(self, table, **conditions):
        found = self.select(table, **conditions)
        answer = False if len(found) == 0 else True
        return answer

##### functions #####
def wait(x, y):
    sleep(uniform(x, y))


def create_directory_for_files(folder):
    """This function creates directory (if doesn't exist) for the files.\n
    :param folder: str, name of creating directory"""
    if not path.exists(getcwd() + folder):
        makedirs(getcwd() + folder)


def cookies_accept():
    """Clicking the 'cookies accept' buttons on the start page"""
    wait(6, 8)
    more_options_cookies_button = browser.find_element_by_xpath('//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
    more_options_cookies_button.click()
    wait(3, 5)  # time sleep generator


def is_element_clickable(element):
    """If the element isn't clickable, the current page waits next 3-4 seconds.\n
    :param element: Element, the element from the current page"""
    if not element_to_be_clickable(element):
        print("The element is not yet clickable. Waiting...")
        wait(20, 30)
    if not element_to_be_clickable(element):
        raise Exception("Unexpected error! The element is not clickable. Script ends: {}".format(asctime(localtime())))


def check_league_and_season(ucl_season, league_name):
    """Preview section on whoscored.com ix available only for few league and correct seasons.
    This function checks this condition and returns anser in bool."""
    if league_name in ['England', 'Spain', 'Germany', 'Italy', 'France']:  # TOP 5 leagues - all seasons available
        return True
    if league_name in ['Netherlands', 'Russia'] and ucl_season in ALL_SEASONS[3:]:  # NED and RUS - from 2013/2014
        return True
    if league_name == 'Turkey' and ucl_season in ALL_SEASONS[4:]:  # Turkey - from 2014/2015
        return True
    if league_name == 'Portugal' and ucl_season in ALL_SEASONS[-4:]:  # Portugal - from 2016/2017
        return True
    if league_name == 'Scotland' and ucl_season in ALL_SEASONS[-3:]:  # Scotland - from 2017/2018
        return True
    return False


def select_season(selected_season):
    """This function selects the correct season from ALL_SEASONS in the drop down menu on the page.\n
    :param selected_season: str, name of options in drop down menu 'season' """
    drop_down_menu = browser.find_element_by_name("seasons")
    select = Select(drop_down_menu)
    is_element_clickable(drop_down_menu)
    wait(1.5, 2.5)
    select.select_by_visible_text(selected_season)
    wait(1.5, 2.5)


def select_stage():
    drop_down_menu = browser.find_element_by_name("stages")
    is_element_clickable(drop_down_menu)
    select = Select(drop_down_menu)
    wait(1.5, 2.5)
    all_options = drop_down_menu.find_elements_by_tag_name("option")
    for option in all_options:
        if str(option.get_attribute("text")) == 'Eredivisie':
            select.select_by_visible_text(option)
            break
    else:
        log.write(f"Probably problem! The correct option not found in drop down menu 'stages'. "
                  f"League: {league}, season: {season}.", level=logging.ERROR)
        print("ERROR The correct option not found in drop down menu 'stages'. League: {league}, season: {season}.")
        sys.exit(1)
    wait(3, 4)


def filtration_team_matches(team_id, links):
    row = db.select("Teams", Team_id=team_id)[0]
    team_name = row['Team_name']
    name_words = team_name.split(" ")
    team_links = links[:]
    for link in links:
        for word in name_words:
            if word not in link:
                del team_links[team_links.index(link)]
                break
    log.write(f"Found matches of team {team_id}.")
    return team_links


def get_link_and_id(html_code) -> (str, str):
    """ This function returns link to webpage with match centre and WhoScored ID of the given match
        in form od two-element tuple. \n
        :param html_code: str, path to the file with match centre"""
    soup = BeautifulSoup(html_code, 'html.parser')
    whoscored_link = soup.find("link", rel="canonical").get("href")
    match_id = whoscored_link.split("/")[4]
    return whoscored_link, match_id


def get_teams(html_code) -> {str}:
    """This function returns WhoScored IDs, names and leagues of both teams in shape of dictionary.
    Keys of the resulting dictionary: 'team1_name', 'team2_name', 'team1_id', 'team2_id',
    'team1_league', 'team2_league'. \n
        :param html_code: str, path to the file with match centre"""
    soup = BeautifulSoup(html_code, 'html.parser')
    teams_ids = soup.find_all("div", class_="pitch-field")
    return teams_ids[0].get("data-team-id"), teams_ids[1].get("data-team-id")  # team_1_ID, team_2_ID


def download_all_links(league, season):
    """This function gets links to all matches of given league and season.
    Returns a list of links. Result of this function is saved in dictionary
    links_league_season and is used for all teams from given league."""
    log.write(f"Starting downloading of matches {league} from season {season}...")
    browser.get(LEAGUES[league])
    wait(1, 2)
    cookies_accept()
    wait(1, 2)
    select_season(season)
    wait(2, 3)
    if len(browser.find_elements_by_name("stages")) != 0:
        select_stage()
    menu_dates = browser.find_element_by_id("date-config-toggle-button")
    is_element_clickable(menu_dates)
    menu_dates.click()
    wait(2, 3)
    year = browser.find_element_by_xpath(
        f'//*[@id="date-config"]/div[1]/div/table/tbody/tr/td[1]/div/table/tbody/tr[1]/td')
    wait(2, 3)
    year.click()
    wait(2, 3)
    months = browser.find_elements_by_xpath(
        '//*[@id="date-config"]/div[1]/div/table/tbody/tr/td[2]/div/table/tbody/tr/td')
    first_month = list(filter(lambda x: "selectable" in x.get_attribute("class"), months))[0]
    first_month.click()
    wait(1, 2)
    weeks = browser.find_elements_by_xpath('//*[@id="date-config"]/div[1]/div/table/tbody/tr/td[3]/div/table/tbody/tr')
    first_week = list(filter(lambda x: "selectable" in x.get_attribute("class"), weeks))[0]
    first_week.click()
    wait(1, 2)
    all_links = []
    next_week = browser.find_element_by_xpath('//*[@id="date-controller"]/a[3]')
    while next_week.get_attribute("title") != "No data for next week":
        wait(4, 5)
        week_matches = browser.find_elements_by_xpath(
            '//*[@id="tournament-fixture"]/div/div/div/a[@class="result-1 rc"]')
        all_links.extend([x.get_attribute("href") for x in week_matches])
        next_week.click()
        print("All Links: ", all_links)
        print("All Links len: ", len(all_links))
        wait(4, 5)
        next_week = browser.find_element_by_xpath('//*[@id="date-controller"]/a[3]')
        print("next week")
    # iteration for last series of matches
    week_matches = browser.find_elements_by_xpath('//*[@id="tournament-fixture"]/div/div/div/a[@class="result-1 rc"]')
    all_links.extend([x.get_attribute("href") for x in week_matches])
    # select only matches for
    with open(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv", "w", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        writer.writerow(links)  # all_links will be saved in case of program error
    log.write(
        f"All links for {league} and {season} downloaded. Saved in file {LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv")
    log.write(f"Number of matches/links: {len(all_links)}")
    return all_links


def get_links_from_file(league, season):
    with open(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv", "r", encoding="utf-8") as csvfile:
        new_links = csvfile.read().strip().split(",")
    log.write(f"Links for league {league} and season {season} downloaded from file.")
    return new_links


def download_matches(team_links, ucl_matches, team_id):
    """browser.execute_script(
        "window.open('');")  # execute_script(script, *args) -> this function synchronously executes JavaScript in the current window/frame.
    browser.switch_to.window(browser.window_handles[1])"""
    log.write(f"Staring downloading of matches for team {team_id}.")
    for link in team_links:
        browser.get(link)
        wait(4, 5)
        log.write(f"The website {link} launched.")
        log.write(browser.title[:-5])
        print(browser.title[:-5])
        match_centre_button = browser.find_element_by_link_text("Match Centre")
        is_element_clickable(match_centre_button)
        match_centre_button.click()
        wait(4, 5)
        try:
            browser.find_element_by_link_text("Preview")
        except NoSuchElementException:
            browser.close()
            log.error(f"Match in link {link} doesn't have 'Preview' section!")
            print(f"WARNING - Match in link {link} doesn't have 'Preview' section!")
            wait(2, 3)
            # browser.switch_to.window(browser.window_handles[0])
            continue
        html_code = browser.page_source
        team_1_id, team_2_id = get_teams(html_code)
        if team_id not in (team_1_id, team_2_id):
            global number_of_downloaded_matches
            log.write(
                f"Error in match with ID {str(number_of_downloaded_matches + 1)}. Contradictory IDs of teams. ID {team_id} vs IDs from site: {team_1_id}, {team_2_id}",
                level=logging.WARNING)
        squad_file = save_file(False, html_code, team_id)  # saving the website with line-up
        log.write(f"File with Match Centre {squad_file} saved.")
        preview_button = browser.find_element_by_link_text("Preview")
        is_element_clickable(preview_button)
        preview_button.click()
        wait(10, 12)
        html_code_preview = browser.page_source
        preview_file = save_file(True, html_code_preview, team_id)  # saving the website with preview
        log.write(f"File with Preview {preview_file} saved.")
        wait(4, 5)
    log.write(f"The end of matches downloading for team: {team_id}")


def save_file(is_preview, html_code, team_id):
    """This function saves the html file with squad.\n
    :param is_preview: bool, defines that currant website contains preview squad or not
    :param html_code: str, contains html code od current downloaded website. """
    global number_of_downloaded_matches
    if not is_preview:
        with open(f"Matches\\{season.replace('/', '_')}\\{league}\\"
                  f"Match_{str(number_of_downloaded_matches + 1)}_squad.html", 'w',
                  encoding="utf-8") as file:
            file.write(str(html_code))
    else:
        with open(f"Matches\\{season.replace('/', '_')}\\{league}\\"
                  f"Match_{str(number_of_downloaded_matches + 1)}_preview.html", 'w', encoding="utf-8") as file:
            file.write(str(html_code))
        number_of_downloaded_matches += 1
    print(f"File {file.name} saved.")
    return file.name


##### Script #####
log = Logger(LOGS_FOLDER)
create_directory_for_files(LINKS_FOLDER)
db = Database(DATABASE)  # connecting to database
number_of_downloaded_matches = len(db.select("Matches"))
log.write(f"Number of already downloaded matches: {number_of_downloaded_matches}")
log.write("Start of matches downloading.")
for season in ALL_SEASONS[0:9]:
    wait(10, 12)
    log.write(f"Current season: {season}")
    all_matches = db.select("UCL_Matches", order_by='UCL_Match_ID', Season=season) # UCL matches of season sorted by id
    for match in all_matches:  # for every UCL match in the season
        team_home = match["team_1_ID"]
        team_away = match["team_2_ID"]

        league = db.select("Teams", Team_ID=team_home)[0]["League"]
        log.write(f"Team: {team_home}. League: {league}")
        if check_league_and_season(season, league):  # if for this league and season section Preview exists
            if path.exists(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv"):
                links_league = get_links_from_file(league, season)
            else:
                links_league = download_all_links(league, season)
            team_home_links = filtration_team_matches(team_home, links_league)
            team_ucl_matches = list(filter(lambda game: game['Team_1_ID'] == team_home or
                                                        game['Team_2_ID'] == team_home, all_matches))

            download_matches(team_home_links, sorted(team_ucl_matches, key=lambda game: game['Date']), team_home)

        league = db.select("Teams", Team_ID=team_away)[0]["League"]
        log.write(f"Team: {team_away}. League: {league}")
        if check_league_and_season(season, league):
            if path.exists(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv"):
                links_league = get_links_from_file(league, season)
            else:
                links_league = download_all_links(league, season)
            team_away_links = filtration_team_matches(team_away, links_league)
