# Copyright (c) Jakub Wilczyński 2020
# Module with key classes in the project.
# classes: Player, Match, Team, Performance

from tools import Database, Logger

from time import sleep
from random import uniform
from bs4 import BeautifulSoup
import sqlite3

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

    def __init__(self, whoscored_id, ucl_match=None, team=None):
        self.whoscored_id = whoscored_id
        self.type = self.type_of_match()
        self.match_id = f"Prev_{self.whoscored_id}_UCL_{ucl_match}" if ucl_match else f"UCL_{self.whoscored_id}"
        Match.matches[self.match_id] = self

        match_data = self.get_match_data_from_db()
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]
        self.league = match_data["League"] if self.type == "Matches" else "UCL"

        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id) if team != match_data[
            "Team_2_ID"] else None
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id) if team != match_data[
            "Team_1_ID"] else None
        print("Object Match created!")

    def __del__(self):
        Match.matches.pop(self.match_id, None)
        print(f"Deleted match {self.match_id} from dict.")

    def __str__(self):
        print(50 * "-")
        print(f"MATCH: {self.team_home.team_name} - {self.team_away.team_name}")
        print(f"Season: {self.season}")
        print(f"Date: {self.date}")
        print(f"League: {self.league}")
        print(f"Centre file: {self.centre_file}")
        print(f"Preview file: {self.preview_file}")
        print(f"Link: {self.link}")
        print(self.team_home)
        print(self.team_away)
        return "#" * 50

    @classmethod
    def create_match(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def delete_all_matches(cls):
        for match_id in list(cls.matches):
            del cls.matches[match_id]

    def type_of_match(self):
        if len(database.select("UCL_Matches", UCL_Match_WhoScored_ID=self.whoscored_id)) != 0:
            return "UCL_Matches"
        elif len(database.select("Matches", Match_Whoscored_ID=self.whoscored_id)) != 0:
            return "Matches"
        else:
            raise Exception(f"Error! Match with ID {self.whoscored_id} doesn't exist.")

    def get_match_data_from_db(self):
        if self.type == "UCL_Matches":
            return database.select(self.type, UCL_Match_WhoScored_ID=self.whoscored_id)[0]
        elif self.type == "Matches":
            return database.select(self.type, Match_WhoScored_ID=self.whoscored_id)[0]
        else:
            raise Exception("Error! Match with this ID (or this table) doesn't exist.")


class Team:
    teams = dict()
    number_last_matches = 5

    def __init__(self, whoscored_id, kind, match_id):  # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.match_id = match_id
        self.match_whoscored_id = Match.matches[self.match_id].whoscored_id
        self.team_id = f"Team_{self.type}_" + str(whoscored_id) + "_" + match_id
        Team.teams[self.team_id] = self

        # getting data about Team from database
        team_data = database.select("Teams", Team_ID=self.whoscored_id)[0]
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]

        # getting data about Team from database or html files
        data = None
        if database.is_element_in_db("Teams_in_" + Match.matches[self.match_id].type, Team_Match_ID=self.whoscored_id):
            data = database.select("Teams_in_" + Match.matches[self.match_id].type, Team_Match_ID=self.whoscored_id)[0]
        self.predicted = self.get_predicted_squad() if data is None else data["Predicted"].split(",")
        self.starting = self.get_lineup() if data is None else data["Starting"].split(",")
        bench = self.get_bench() if data is None else (data["Bench"], data["Substitutes"])
        self.bench = bench[0]
        self.substitutes = bench[1]
        self.missing = self.get_missing_players() if data is None \
            else {player.split(":")[0]: player.split(":")[1] for player in data["Missing"].split(",")}
        self.all_squad = list(set(self.predicted + self.starting + self.bench + list(self.missing.keys())))

        if Match.matches[self.match_id].type == "UCL_Matches":
            self.prev_matches = self.get_prev_matches()
            if data is None:
                self.save_team_UCL_into_db()
            if self.team_name == "Inter":
                print("SAVE DATA INTER NOT WORKS")
            self.players = {idx: Performance(idx, self.team_id) for idx in self.all_squad}
            """
            for prev_match_id in self.prev_matches:
                Match.create_match(prev_match_id, ucl_match=self.match_whoscored_id, team=self.whoscored_id) """
        else:
            self.save_team_into_db()
        # else:
        #   self.players = {idx: Prev_Performance(idx, self.team_id) for idx in self.all_squad}

    def __del__(self):
        Team.teams.pop(self.team_id, None)

    def __str__(self):
        print(50 * "-")
        print(f"TEAM: {self.team_name} ({self.whoscored_id})")
        print(f"Type: {self.type}")
        print(f"Team_ID: {self.team_id}")
        print(f"League: {self.league}")
        print(f"Link: {self.link}")
        print(f"Predicted: {self.predicted}")
        print(f"Starting: {self.starting}")
        print(f"Bench: {self.bench}")
        print(f"All squad: {self.all_squad}")
        print(f"Substitutions: {self.substitutes}")
        print(f"Missing: {self.missing}")
        print(f"Players: {list(self.players)}")
        print(f"Number of players: {len(list(self.players))}")
        print(f"Prev matches: {self.prev_matches}")
        map(lambda x: print(x), self.players)
        return ""

    @classmethod
    def create_team(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def delete_all_teams(cls):
        for team_id in list(cls.teams):
            del cls.teams[team_id]

    def save_team_UCL_into_db(self):
        miss = ",".join([f"{k}:{v}" for k, v in self.missing.items()]) if len(self.missing.keys()) != 0 else "-"
        subs = ",".join(self.substitutes) if len(self.substitutes) != 0 else "-"
        prev_matches = ",".join(self.prev_matches) if len(self.prev_matches) != 0 else "-"
        database.insert("Teams_in_UCL_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), subs, miss, prev_matches)  # (...)
        print("DATA TEAM FUNCTION SAVE")

    def save_team_into_db(self):
        miss = ",".join([f"{k}:{v}" for k, v in self.missing.items()]) if len(self.missing.keys()) != 0 else "-"
        subs = ",".join(self.substitutes) if len(self.substitutes) != 0 else "-"
        database.insert("Teams_in_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), subs, miss)  # (...)

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
            for tr_elem in tbody_element.find_all("tr")[1 - num:]:  # if home -> count from 1, if away -> count from 0
                try:
                    player_id = tr_elem.find("td", class_="pn").find("a", class_="player-link").get("href").split("/")[
                        2]
                    player_status = tr_elem.find("td", class_="confirmed").string
                except AttributeError:
                    break
                missing[player_id] = player_status
            return missing

    def get_prev_matches(self):
        all_prev_matches = [prev_match['Match_WhoScored_ID'] for prev_match
                            in database.select("UCL_Matches_Matches", UCL_Match_WhoScored_ID=self.match_whoscored_id)]
        team_prev_matches = []
        for match in all_prev_matches:
            team_match = database.cursor.execute(
                f'SELECT * FROM Matches WHERE (Team_1_ID={self.whoscored_id} OR Team_2_ID={self.whoscored_id}) '
                f'AND Match_WhoScored_ID={match} ORDER BY Date DESC').fetchall()
            if len(team_match) > 0:
                team_prev_matches.append(str(team_match[0]['Match_WhoScored_ID']))
        return team_prev_matches

    """def get_positions_websites(self):
        pass"""


class Performance:
    players = dict()

    def __init__(self, player_id, team_id):
        self.whoscored_id = player_id
        self.team_id = team_id  # object in form <team_id>_<ucl_match_id>
        self.match_id = Team.teams[team_id].match_id
        self.ucl_match_id = team_id.split("_")[-1]
        self.performance_id = str(self.whoscored_id) + "_" + str(self.ucl_match_id)     # Performance ID
        Performance.players[self.performance_id] = self

        if not database.is_element_in_db("Players", Player_WhoScored_ID=self.whoscored_id):
            self.save_player_data_into_db()
        data = database.select("Players", Player_WhoScored_ID=self.whoscored_id)[0]

        self.name = data["Name"]
        self.link = data["Link"]
        self.predicted = 1 if self.in_predicted_squad() else 0
        self.starting = 1 if self.in_lineup() else 0
        self.substitute = 1 if self.is_substitute() else 0
        self.bench_no_sub = 1 if self.on_bench() and self.substitute == 0 else 0
        self.missing = self.is_missing()
        if not database.is_element_in_db("Performances", Performance_ID=self.performance_id):
            self.save_performance_data_into_db()

    def __del__(self):
        Performance.players.pop(self.performance_id, None)

    def __str__(self):
        print(50 * "-")
        print(f"PLAYER: {self.name} ({self.whoscored_id})")
        print(f"Performance_ID: {self.performance_id}")
        print(f"Link: {self.link}")
        print(f"Predicted: {self.predicted}")
        print(f"Starting: {self.starting}")
        print(f"Substitute: {self.substitute}")
        print(f"On bench but no sub: {self.bench_no_sub}")
        print(f"Missing: {self.missing}")
        return "*" * 50

    @classmethod
    def create_performance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def delete_all_performances(cls):
        for performance_id in list(cls.players):
            del cls.players[performance_id]

    def save_player_data_into_db(self):
        player_name = ''
        for website in (Match.matches[self.match_id].centre_file, Match.matches[self.match_id].preview_file):
            with open(website, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                player_div = soup.find("div", attrs={"class": "player", "data-player-id": self.whoscored_id})
                if player_div is not None:
                    player_name = player_div.find("div", attrs={"class": "player-name-wrapper"})['title']
                    break
                player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": self.whoscored_id})
                if player_ul is not None:
                    player_name = player_ul['title'].split("(")[0]
                for player_miss in soup.find_all("a", class_="player-link"):
                    if str(self.whoscored_id) in player_miss['href']:
                        player_name = player_miss.string
        if player_name == '':
            raise Exception(
                f"Error! Name of player with ID {self.whoscored_id} for match {self.ucl_match_id} not downloaded...")
        database.insert("Players", True, self.whoscored_id, player_name,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")

    def save_performance_data_into_db(self):
        """update needed"""
        database.insert("Performances", True, self.performance_id, self.whoscored_id, self.name, self.team_id,
                        self.predicted, self.starting, self.bench_no_sub, self.substitute, self.missing)

    def is_missing(self):
        status = ''
        for p_id, value in Team.teams[self.team_id].missing.items():
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
        if self.whoscored_id in Team.teams[self.team_id].substitutes:
            return True
        return False

    @staticmethod
    def from_bool_to_int(boolean):
        change = {False: '0', True: '0'}
        return change[boolean]


class Prev_Performance:
    prev_players = dict()

    def __init__(self, player_id, team_id):
        self.prev_team_id = team_id
        self.match_id = Team.teams[self.prev_team_id].match_id
        self.whoscored_id = player_id
        self.team_id = team_id  # object in form <team_id>_<ucl_match_id>
        self.ucl_performance_id = Team.teams[self.prev_team_id].players[self.whoscored_id].performance_id
        self.prev_performance_id = "Prev_" + str(self.whoscored_id) + "_" + str(self.match_id)
        Prev_Performance.prev_players[self.prev_performance_id] = self

        if not database.is_element_in_db("Players", Player_WhoScored_ID=self.whoscored_id):
            self.save_player_data_into_db()
        data = database.select("Players", Player_WhoScored_ID=self.whoscored_id)[0]
        self.name = data["Name"]
        self.link = data["Link"]

        self.predicted = 1 if self.in_predicted_squad() else 0
        self.starting = 1 if self.in_lineup() else 0
        self.substitute = 1 if self.is_substitute() else 0
        self.bench_no_sub = 1 if self.on_bench() and self.substitute == 0 else 0
        self.missing = self.is_missing()
        if not database.is_element_in_db("Performances", Performance_ID=self.performance_id):
            self.save_performance_data_into_db()

    def __del__(self):
        Prev_Performance.prev_players.pop(self.performance_id, None)

    def __str__(self):
        print(50 * "-")
        print(f"PLAYER: {self.name} ({self.whoscored_id})")
        print(f"Performance_ID: {self.performance_id}")
        print(f"Link: {self.link}")
        print(f"Predicted: {self.predicted}")
        print(f"Starting: {self.starting}")
        print(f"Substitute: {self.substitute}")
        print(f"On bench but no sub: {self.bench_no_sub}")
        print(f"Missing: {self.missing}")
        return "*" * 50

    @classmethod
    def create_prev_performance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def delete_all_prev_performances(cls):
        for prev_performance_id in list(cls.players):
            del cls.players[prev_performance_id]

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

    def save_prev_performance_data_into_db(self):
        """update needed"""
        database.insert("Prev_Performances", True, self.prev_performance_id, self.whoscored_id, self.name, self.team_id,
                        self.predicted, self.starting, self.bench_no_sub, self.substitute, self.missing)


print("Module classes.py imported.")
test = Match.create_match("458711")
print(test)
