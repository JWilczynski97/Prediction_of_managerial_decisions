# Copyright (c) Jakub Wilczyński 2020
# Module with key classes in the project.
# classes: Player, Match, Team, Performance

from tools import Database, Logger

from time import sleep
from random import uniform
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.common.exceptions import NoSuchElementException

###### WEB DRIVER OPTIONS #####
options = Options()
options.add_argument('start-maximized')  # maximize of the browser window
options.add_experimental_option("excludeSwitches",
                                ['enable-automation'])  # process without information about the automatic test
options.add_argument("chrome.switches")
options.add_argument("--disable-extensions")
""" browser = webdriver.Chrome(executable_path='Chromedriver\chromedriver.exe', options=options)
 browser.get(self.link)
 sleep(uniform(2,3))
 try:
     more_options_cookies_button = browser.find_element_by_xpath('//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
     is_element_clickable(more_options_cookies_button)
     more_options_cookies_button.click()
 except NoSuchElementException:
     pass
 sleep(uniform(2, 3)) """

##### DATABASE #####
database = Database("Matches_DB_copy.db", logger=Logger(std_output=True))


class Match:
    matches = dict()

    def __init__(self, whoscored_id):
        self.whoscored_id = whoscored_id
        self.type = self.type_of_match()
        match_data = self.get_match_data_from_db()
        # self.match_id = match_data["Match_ID"]
        self.team_home = Team(match_data["Team_1_ID"], "home", self.whoscored_id)
        self.team_away = Team(match_data["Team_2_ID"], "away", self.whoscored_id)
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]
        self.league = match_data["League"] if self.type == "Matches" else "UCL"

        Match.matches[self.whoscored_id] = self

    def __del__(self):
        del Match.matches[self.whoscored_id]

    def type_of_match(self):
        if len(database.select("UCL_Matches", Match_Whoscored_ID=self.whoscored_id)) != 0:
            return "UCL_Matches"
        elif len(database.select("Matches", Match_Whoscored_ID=self.whoscored_id)) != 0:
            return "Matches"
        else:
            raise Exception("Error! Match with this ID doesn't exist.")

    def get_match_data_from_db(self):
        if self.type == "UCL_Matches":
            return database.select(self.type, UCL_Match_WhoScored_ID=self.whoscored_id)[0]
        elif self.type == "Matches":
            return database.select(self.type, Match_WhoScored_ID=self.whoscored_id)[0]
        else:
            raise Exception("Error! Match with this ID (or this table) doesn't exist.")


class Team:
    teams = dict()  # one of teams in a match

    def __init__(self, whoscored_id, kind, match_id):  # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.match_id = match_id
        self.team_id = str(whoscored_id) + "_" + str(match_id)

        team_data = database.select("Teams", Team_ID=self.whoscored_id)
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]

        bench = self.get_bench()
        self.predicted = self.get_predicted_squad()
        self.starting = self.get_start_squad()
        self.bench = bench[0]
        self.substitutes = bench[1]
        self.missing_players = self.get_missing_players()
        self.all_squad = list(set(*self.predicted, *self.starting, *self.bench, *self.missing_players))

        if Match.matches[self.match_id].type == "UCL_Matches":
            self.players = {idx: Performance(idx, self.team_id) for idx in self.all_squad}
            self.prev_matches = self.get_prev_matches()

        # else:
        #   self.players = {idx: Prev_Performance(idx, self.team_id) for idx in self.all_squad}
        Team.teams[self.whoscored_id] = self

    def __del__(self):
        del Team.teams[self.team_id]

    def save_team_into_db(self):
        database.insert("Teams_in_UCL_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench))  # (...)

    def get_predicted_squad(self):
        with open(Match.matches[self.match_id].preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            all_elements = soup.find_all("ul", class_="player")
            all_predicted = []
            for player in all_elements:
                all_predicted.append(player.get('data-playerid'))
            team_preview = all_predicted[:11] if self.type == "home" else all_predicted[11:]
            return team_preview

    def get_lineup(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(Match.matches[self.match_id].centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            pitch_element = soup.find_all("div", class_="pitch-field")
            team_squad = []
            team_elements = pitch_element[num].find_all("div", class_="player")
            for player in team_elements:
                team_squad.append(player.get('data-player-id'))
            return team_squad

    def get_bench(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(Match.matches[self.match_id].centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            bench_element = soup.find_all("div", class_="substitutes")
            team_bench, team_substitues = list(), list()
            team_elements = bench_element[num].find_all("div", class_="player")
            for player in team_elements:
                team_bench.append(player.get('data-player-id'))
                if player.get('data-subbed-in') == "true":
                    team_substitues.append(player.get('data-player-id'))
            return team_bench, team_substitues

    def get_missing_players(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(Match.matches[self.match_id].preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            tbody_element = soup.find_all("tbody")[num]
            missing = dict()
            for tr_elem in tbody_element.find_all("tr"):
                player_id = tr_elem.find("td", class_="pn").get("href").split("/")[2]
                player_status = tr_elem.find("td", class_="confirmed").string
                missing[player_id] = player_status
            return missing

    def get_prev_matches(self):
        all_prev_matches = [prev_match['Match_WhoScored_ID'] for prev_match
                            in database.select("UCL_Matches_Matches", order_by="Date", option_order="DESC",
                                               UCL_Match_WhoScored_ID=self.match_id)]
        team_prev_matches = []
        for match in all_prev_matches:
            team_match = database.cursor.execute(
                f'SELECT * FROM Matches WHERE (Team_1_ID={self.whoscored_id} OR Team_2_ID={self.whoscored_id}) '
                f'AND Match_WhoScored_ID={match} ORDER BY Date DESC')
            if len(team_match) > 0:
                team_prev_matches.append(team_match[0])
        return team_prev_matches

    """def get_positions_websites(self):
        pass"""


class Performance:
    players = dict()

    def __init__(self, player_id, team_id):
        self.whoscored_id = player_id
        self.team_id = team_id  # object in form <team_id>_<ucl_match_id>
        self.ucl_match_id = team_id.split("_")[1]
        self.performance_id = str(self.whoscored_id) + "_" + str(self.ucl_match_id)
        if not database.is_element_in_db("Players", Player_WhoScored_ID=self.whoscored_id):
            self.save_player_data_into_db()
        data = database.select("Players", Player_WhoScored_ID=self.player_id)

        self.name = data["Name"]
        self.link = data["Link"]
        self.predicted = 1 if self.in_predicted_squad() else 0
        self.starting = 1 if self.in_lineup() else 0
        self.substitute = 1 if self.is_substitute() else 0
        self.bench_no_sub = 1 if self.on_bench() and self.substitute == 0 else 0
        self.missing = self.is_missing()
        Performance.players[self.performance_id] = self

    def __del__(self):
        del Performance.players[self.performance_id]

    def save_performance_into_db(self):  # table Performances: Performance_ID, Player_ID, UCL_Match_ID, Missing
        """update this method"""
        database.insert("Performances", self.performance_id, self.player_id, self.match_id, self.missing)  # ...

    def save_player_data_into_db(self):
        player_name = ''
        for website in (Match.matches[self.ucl_match_id].centre_file, Match.matches[self.ucl_match_id].preview_file):
            with open(website, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                player_div = soup.find("div", attrs={"class": "player", "data-player-id": self.whoscored_id})
                if player_div is not None:
                    player_name = player_div.find("div", attrs={"class": "player-name-wrapper"})['title']
                    break
                player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": self.whoscored_id})['title']
                if player_ul is not None:
                    player_name = player_ul.split("(")[0]
                for player_miss in soup.find_all("a", class_="player-link"):
                    if str(self.whoscored_id) in player_miss['href']:
                        player_name = player_miss.string
        if player_name == '':
            raise Exception(
                f"Error! Name of player with ID {self.whoscored_id} for match {self.ucl_match_id} not downloaded...")
        database.insert("Players", True, self.whoscored_id, player_name,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")

    def is_missing(self):
        status = ''
        for p_id, value in Team.teams[self.team_id].missing_players.items():
            if p_id == self.whoscored_id:
                status = value
        if status == '':
            return 0
        elif status == "Doubtful":
            return 1
        elif status == "Out":
            return 2
        else:
            raise Exception(f"Error! Unknown status of missing player {self.whoscored_id} in {self.match_id}")

    def in_predicted_squad(self):
        if self.whoscored_id in Team.teams[self.team_id].predicted:
            return True
        return False

    def in_lineup(self):
        if self.whoscored_id in Team.teams[self.team_id].starting:
            return True
        return False

    def on_bench(self):
        if self.whoscored_id in Team.teams[self.team_id].bench:
            return True
        return False

    def is_substitute(self):
        if self.whoscored_id in Team.teams[self.team_id].substitue:
            return True
        return False

    @staticmethod
    def from_bool_to_int(boolean):
        change = {False: '0', True: '0'}
        return change[boolean]


class Prev_Performance:
    prev_players = dict()

    def __init__(self, performance_id, match_id):
        self.ucl_performance = Performance.players[performance_id]
        self.match_id = match_id
        self.performance_id = self.match_id + "_" + self.ucl_performance.name
        self.team_id = team_id  # object in form <team_id>_<ucl_match_id>
        self.match_id = team_id.split("_")[1]
        self.performance_id = str(self.whoscored_id) + "_" + str(self.ucl_match_id)

        # self.predicted = 1 if PrevPerformance.in_predicted_squad(self) else 0
        Performance.players[self.performance_id] = self

    def save_player_data_into_db(self):
        name_player = ''
        for website in (Match.matches[self.match_id].centre_file, Match.matches[self.match_id].preview_file):
            with open(website, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                player_div = soup.find("div", attrs={"class": "player", "data-player-id": self.whoscored_id})
                if player_div is not None:
                    name_player = player_div.find("div", attrs={"class": "player-name-wrapper"})['title']
                    break
                player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": self.whoscored_id})['title']
                if player_ul is not None:
                    name_player = player_ul.split("(")[0]
                for player_miss in soup.find_all("a", class_="player-link"):
                    if str(self.whoscored_id) in player_miss['href']:
                        name_player = player_miss.string
        if name_player == '':
            raise Exception(
                f"Error! Name of player with ID {self.whoscored_id} for match {self.ucl_match_id} not downloaded...")
        database.insert("Players", True, self.whoscored_id, name_player,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")


print("Module classes.py imported.")
