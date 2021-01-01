# Copyright (c) Jakub Wilczyński 2020
# The task of this program is downloading of WhoScored.com webpages with starting and predicted line-ups in european
# football leagues for teams playing in UEFA Champions League in seasons 2010/2011 to 2019/2020. Data about
# these games will be used to predict of managerial decisions in the next steps of project. Data about matches
# are saving into the SQLite database on the local disk. Every game is assigned to the correct UCL matches
# taking place after this league match in the same season. The html codes of these websites are saved to
# the html files in specified folders on the local disk.
# Tools used: Python 3.8, Selenium Webdriver 3.141.0, BeautifulSoup  4.9.1, SQLite 3.28.0

from tools import Database, Logger

from os import path, getcwd, makedirs
import logging
import datetime
from sys import stdout
import csv
import sqlite3 as lite
from time import asctime, localtime, sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from bs4 import BeautifulSoup
from random import uniform

###### WEBDRIVER OPTIONS #####
OPTIONS = Options()
OPTIONS.add_argument('start-maximized')  # maximize of the browser window
OPTIONS.add_experimental_option("excludeSwitches",
                                ['enable-automation'])  # process without information about the automatic test
OPTIONS.add_argument("chrome.switches")
OPTIONS.add_argument("--disable-extensions")
DRIVER_PATH = 'Chromedriver\chromedriver.exe'   # path to the webdriver file

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
MATCHES_FOLDER = 'Matches'
LOGS_FOLDER = 'Logs'        # directory for files with logs of program
LINKS_FOLDER = 'Links'      # directory for text files with links to matches of european leagues
DATABASE = 'Matches_DB_copy.db'  # .db file with SQLite database

##### functions #####
def wait(x, y):
    """This function launches sleep function for a few seconds.
    Number of seconds is a random floating point number x to y.\n
    :param x: int, start of interval
    :param y: int, end of interval"""
    sleep(uniform(x, y))


def create_directory_for_files(folder):
    """This function creates directory (if doesn't exist) for the files.\n
    :param folder: str, name of creating directory"""
    if not path.exists(getcwd() + folder):
        makedirs(getcwd() + folder)


def cookies_accept():
    """Function to click the 'cookies accept' buttons on the page if they exist."""
    try:
        more_options_cookies_button = browser.find_element_by_xpath('//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
        is_element_clickable(more_options_cookies_button)
        more_options_cookies_button.click()
    except NoSuchElementException:
        pass
    wait(3, 5)  # time sleep generator


def is_element_clickable(element):
    """If the element isn't clickable, the current page waits one time or raises Exception..\n
    :param element: Element, the element from the current page"""
    if not element_to_be_clickable(element):
        log.write("The element is not yet clickable. Waiting...")
        wait(8, 10)
    if not element_to_be_clickable(element):
        log.write("Unexpected error! The element is not clickable.")
        raise Exception("Unexpected error! The element is not clickable.")


def check_league_and_season(ucl_season, league_name):
    """Preview section on whoscored.com is available only for few league and correct seasons.
    This function checks this condition and returns answer True/False. \n
    :param ucl_season: str, name of checked season
    :param league_name: str, name of checked league"""
    if league_name in ['England', 'Spain', 'Germany', 'Italy', 'France']:  # TOP 5 leagues - all seasons with available Preview section
        return True
    if league_name in ['Netherlands', 'Russia'] and ucl_season in ALL_SEASONS[3:]:  # NED and RUS - from 2013/2014
        return True
    if league_name == 'Turkey' and ucl_season in ALL_SEASONS[4:]:  # Turkey - from 2014/2015
        return True
    if league_name == 'Portugal' and ucl_season in ALL_SEASONS[-4:]:  # Portugal - from 2016/2017
        return True
    if league_name == 'Scotland' and ucl_season in ALL_SEASONS[-3:]:  # Scotland - from 2017/2018
        return True     # update: no matches of scotisch teams in UCL in these seasons == no downloaded matches
    return False


def select_season(selected_season):
    """This function selects the correct season from ALL_SEASONS in the drop down menu on the page.\n
    :param selected_season: str, name of options in drop down menu 'season'"""
    drop_down_menu = browser.find_element_by_name("seasons")
    select = Select(drop_down_menu)
    is_element_clickable(drop_down_menu)
    wait(1.5, 2.5)
    select.select_by_visible_text(selected_season)
    wait(1.5, 2.5)


def select_stage():
    """This function selects the stage in the drop down menu on the page (if element 'stage' exists)."""
    drop_down_menu = browser.find_element_by_name("stages")
    is_element_clickable(drop_down_menu)
    select = Select(drop_down_menu)
    wait(1.5, 2.5)
    try:
        select.select_by_visible_text('Eredivisie') # only case with 'stage' element existing is dutch league Eredivisie
    except NoSuchElementException as e:
        log.write(f"League: {league}, season: {season}. Probably problem! The correct option can be not found in drop down menu 'stages'.", level=logging.ERROR)
        log.write(f"Error: {e}.", level=logging.ERROR)
        sys.exit(1)
    wait(3, 4)


def filtration_team_matches(team_id, links):
    """This function selects links to the webpages with matches of given team from list of all league links."""
    row = db.select("Teams", Team_id=team_id)[0]
    name = row['Team_name']
    name_words = name.strip().split(" ")
    name = "-".join(name_words)
    for link in links[:]:
        if str(name) not in link:
            del links[links.index(link)]
    log.write(f"Filtration ended. Found matches of team {team_id}. Number of matches: {len(links)}. Matches: {links}")
    return links


def get_link_and_id(html_code):
    """ This function returns link to webpage with match centre and WhoScored ID of the given match
        in form od two-element tuple. \n
        :param html_code: str, path to the file with match centre"""
    soup = BeautifulSoup(html_code, 'html.parser')
    whoscored_link = soup.find("link", rel="canonical").get("href")
    match_id = whoscored_link.split("/")[4]
    return whoscored_link, match_id


def get_teams(html_code):
    """This function returns WhoScored IDs, names and leagues of both teams in shape of dictionary.
    Keys of the resulting dictionary: 'team1_name', 'team2_name', 'team1_id', 'team2_id',
    'team1_league', 'team2_league'. \n
        :param html_code: str, path to the file with match centre"""
    soup = BeautifulSoup(html_code, 'html.parser')
    teams_ids = soup.find_all("div", class_="pitch-field")
    return teams_ids[0].get("data-team-id"), teams_ids[1].get("data-team-id")  # team_1_ID, team_2_ID


def get_date(html_code):
    """This function returns date of match from Match Centre webpage in the format yyyy-mm-dd. \n
        :param html_code: str"""
    soup = BeautifulSoup(html_code, 'html.parser')
    game_date = soup.find_all("div", class_="info-block cleared")[2].find_all("dd")[1].string[5:]
    assert len(game_date) == 9
    day, month, year = game_date.split("-")
    game_date = datetime.date(int("20" + year), MONTHS[month], int(day))
    return str(game_date)


def download_all_league_links(league_name, season_name):
    """This function gets links to all matches of given league and season.
    Returns a list of links. Results of this function are saved in files
     <league>_<season>.csv in directory LINKS_FOLDER and are used for all teams from given league."""
    log.write(f"Starting downloading of matches {league_name} from season {season_name}...")
    browser.get(LEAGUES[league_name])
    wait(1, 2)
    cookies_accept()
    select_season(season_name)
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
        wait(3, 4)
        week_matches = browser.find_elements_by_xpath(
            '//*[@id="tournament-fixture"]/div/div/div/a[@class="result-1 rc"]')
        all_links.extend([x.get_attribute("href") for x in week_matches])
        next_week.click()
        log.write("Links downloading... Next week.")
        wait(2, 3)
        next_week = browser.find_element_by_xpath('//*[@id="date-controller"]/a[3]')
    # iteration for last series of matches
    week_matches = browser.find_elements_by_xpath('//*[@id="tournament-fixture"]/div/div/div/a[@class="result-1 rc"]')
    all_links.extend([x.get_attribute("href") for x in week_matches])
    # select only matches for
    with open(f"{LINKS_FOLDER}\\{league_name}_{season_name.replace('/', '_')}.csv", "w", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        writer.writerow(all_links)  # all_links will be saved in case of program error
    log.write(
        f"All links for {league_name} and {season_name} downloaded. Saved in file {LINKS_FOLDER}\\{league_name}_{season_name.replace('/', '_')}.csv")
    log.write(f"Number of matches/links: {len(all_links)}")
    return all_links


def get_links_from_file(league_name, season_name):
    """This function gets a list of links to the matches for given league and season from files on the local disk."""
    with open(f"{LINKS_FOLDER}\\{league_name}_{season_name.replace('/', '_')}.csv", "r", encoding="utf-8") as csvfile:
        new_links = csvfile.read().strip().split(",")
    log.write(f"Links for league {league_name} and season {season_name} downloaded from file. Number of links: {len(new_links)}")
    return new_links

def check_downloaded_teams(id_team, name_season):
    """This function checks that the matches of given team from given season are already downloaded.
    Returns the answer as True/False"""
    if path.exists(f"{LINKS_FOLDER}\\downloaded_teams_{name_season.replace('/', '_')}.txt"):
        with open(f"{LINKS_FOLDER}\\downloaded_teams_{name_season.replace('/', '_')}.txt", "r", encoding="utf-8") as f:
            answer = True if f"--{str(id_team)}--" in f.read() else False
            if answer is True:
                log.write(f"The matches of team {id_team} in season {name_season} have already been downloaded. Skip!")
            return answer
    return False

def download_matches(season_, league_, team_links, ucl_matches, team_id):
    """This function downloads webpages with Preview and Match Centre sections of every league match for given team.
    The data about every match are saved into the DATABASE. \n
    :param season_: str, current analyzed season
    :param league_: str, name of league
    :param team_links: list, links of league matches for given team
    :param ucl_matches: list, list of UCL matches for given team
    :param team_id: WhoScored ID of the team"""
    log.write(f"Starting downloading of matches for team {team_id} in season {season_}.")
    for link in team_links[:]:
        # if the match is already downloaded, we delete it from links and add new rows into 'UCL_Matches_Matches' table (if don't exist)
        if db.is_element_in_db("Matches", Link=link):
            league_match = db.select("Matches", Link=link)[0]
            for ucl_match in ucl_matches:
                if ucl_match['Date'] > league_match['Date'] \
                        and not db.is_element_in_db('UCL_Matches_Matches',
                                                    UCL_Match_WhoScored_ID=ucl_match['UCL_Match_WhoScored_ID'],
                                                    Match_WhoScored_ID=league_match['Match_WhoScored_ID'],
                                                    Season=season_):
                    db.insert('UCL_Matches_Matches', ucl_match['UCL_Match_WhoScored_ID'],
                              league_match['Match_WhoScored_ID'], season_)
            log.write(f"The match in {link} is already downloaded. Added rows with this match to to 'UCL_Matches_Matches'. Skip.")
            del team_links[team_links.index(link)]
    create_directory_for_files(f"Matches\\{season_.replace('/','_')}\\{league_}")
    last_ucl_match_date = ucl_matches[-1]['Date']

    for link in team_links:
        browser.get(link)
        log.write(f"The website {link} launched.")
        wait(3, 4)
        cookies_accept()
        log.write(browser.title[:-5])
        wait(2, 3)
        try:
            browser.find_element_by_link_text("Preview")
        except NoSuchElementException:
            log.write(f"Match in link {link} doesn't have 'Preview' section!", logging.ERROR)
            wait(2, 3)
            continue

        # taking data from html_code
        html_code = browser.page_source
        match_date = get_date(html_code)
        if match_date >= last_ucl_match_date:
            log.write(f"The end. Match in link {link} isn't important league match for team {team_id} in season {season_}")
            wait(2, 3)
            break
        team_1_id, team_2_id = get_teams(html_code)
        match_link, whoscored_id = get_link_and_id(html_code)
        if str(team_id) not in (team_1_id, team_2_id):
            global number_of_downloaded_matches
            log.write(
                f"Error in match with ID {str(number_of_downloaded_matches + 1)}. Link: {link}. Contradictory IDs of teams. ID {team_id} vs IDs from site: {team_1_id}, {team_2_id}",
                level=logging.WARNING)

        squad_file = save_file(False, html_code, season_, league_)  # saving the website with line-up
        match_idx = squad_file.split("_")[2]
        log.write(f"File with Match Centre {squad_file} saved.")
        preview_button = browser.find_element_by_link_text("Preview")
        is_element_clickable(preview_button)
        preview_button.click()
        wait(8, 10)
        html_code_preview = browser.page_source
        preview_file = save_file(True, html_code_preview, season_, league_)  # saving the website with preview
        log.write(f"File with Preview {preview_file} saved.")

        # adding match to the table "Matches"
        db.insert("Matches", match_idx, team_1_id, team_2_id, season_, league_, whoscored_id, match_date, squad_file,
                  preview_file, match_link)
        wait(4, 5)
        for ucl_match in ucl_matches:
            if ucl_match['Date'] > match_date \
                    and not db.is_element_in_db("UCL_Matches_Matches",
                                                UCL_Match_WhoScored_ID=ucl_match['UCL_Match_WhoScored_ID'],
                                                Match_WhoScored_ID=whoscored_id, Season=season_):
                db.insert("UCL_Matches_Matches", ucl_match['UCL_Match_WhoScored_ID'], whoscored_id, season_)
        log.write("The link downloaded. Next...")

    log.write(f"The end of matches downloading for team: {team_id} in season {season_}")
    with open(f"{LINKS_FOLDER}\\downloaded_teams_{season_.replace('/', '_')}.txt", "a", encoding="utf-8") as f:
        f.write(f"--{str(team_id)}--|") # ID of team with already downloaded matches is writing to the file


def save_file(is_preview, html_code, season__, league__):
    """This function saves the html code of webpage to the file.\n
    :param is_preview: bool, defines that currant website contains preview squad or not
    :param html_code: str, contains html code of current downloaded website.
    :param season__: str, current analyzed season
    :param league__: str, current analyzed league"""
    global number_of_downloaded_matches
    if not is_preview:
        with open(f"{MATCHES_FOLDER}\\{season__.replace('/', '_')}\\{league__}\\"
                  f"Match_{str(number_of_downloaded_matches + 1)}_squad.html", 'w',
                  encoding="utf-8") as file:
            file.write(str(html_code))
    else:
        with open(f"{MATCHES_FOLDER}\\{season__.replace('/', '_')}\\{league__}\\"
                  f"Match_{str(number_of_downloaded_matches + 1)}_preview.html", 'w', encoding="utf-8") as file:
            file.write(str(html_code))
        number_of_downloaded_matches += 1
    return file.name


##### Script #####
browser = webdriver.Chrome(executable_path=DRIVER_PATH, options=OPTIONS)
log = Logger(LOGS_FOLDER, std_output=True)
create_directory_for_files(LOGS_FOLDER)
create_directory_for_files(LINKS_FOLDER)
db = Database(DATABASE, logger=log)  # connecting to database
number_of_downloaded_matches = len(db.select("Matches"))
log.write(f"Number of already downloaded matches: {number_of_downloaded_matches}")
log.write("Start of league matches downloading.")
restart_counter = 0

for season in ALL_SEASONS:
    log.write(f"Current season: {season}")
    all_matches = db.select("UCL_Matches", order_by='UCL_Match_ID', Season=season)  # UCL matches of season sorted by id
    for match in all_matches:  # for every UCL match in the season
        team_home = match["team_1_ID"]
        team_away = match["team_2_ID"]

        team = db.select("Teams", Team_ID=team_home)[0]
        league = team["League"]
        team_name = team["Team_name"]
        log.write(f"IDx: {match['UCL_Match_ID']}. UCL Match: {match['UCL_Match_WhoScored_ID']}. Team home: {team_name}. Team ID: {team_home}. League: {league}")
        if check_league_and_season(season, league) and not check_downloaded_teams(team_home, season):  # if for this league and season section Preview exists
            if path.exists(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv"):
                links_league = get_links_from_file(league, season)
            else:
                links_league = download_all_league_links(league, season)
            team_home_links = filtration_team_matches(team_home, links_league)
            team_ucl_matches = list(filter(lambda game: team_home in (game['Team_1_ID'], game['Team_2_ID']), all_matches))
            download_matches(season, league, team_home_links, sorted(team_ucl_matches, key=lambda game: game['Date']), team_home)
            restart_counter += 1

        team = db.select("Teams", Team_ID=team_away)[0]
        league = team["League"]
        team_name = team["Team_name"]
        log.write(f"IDx: {match['UCL_Match_ID']}. UCL Match: {match['UCL_Match_WhoScored_ID']}. Team away: {team_name}. Team ID: {team_away}. League: {league}")
        if check_league_and_season(season, league) and not check_downloaded_teams(team_away, season):
            if path.exists(f"{LINKS_FOLDER}\\{league}_{season.replace('/', '_')}.csv"):
                links_league = get_links_from_file(league, season)
            else:
                links_league = download_all_league_links(league, season)
            team_away_links = filtration_team_matches(team_away, links_league)
            team_ucl_matches = list(filter(lambda game: team_away in (game['Team_1_ID'], game['Team_2_ID']), all_matches))
            download_matches(season, league, team_away_links, sorted(team_ucl_matches, key=lambda game: game['Date']), team_away)
            restart_counter += 1

        if restart_counter > 2:     # restart browser after matches downloading of 3 teams -> for improved program performance
            restart_counter = 0
            browser.close()
            log.write("Stop! Restart browser. Wait 1 minute...")
            wait(50, 60)
            browser = webdriver.Chrome(executable_path=DRIVER_PATH, options=OPTIONS)

browser.close()
