# Copyright (c) Jakub Wilczyński 2020
# Module with key classes in the project.
# classes: Player, Match, Team, Performance

from tools import Database, Logger

from time import sleep, asctime
import datetime
from random import uniform
from bs4 import BeautifulSoup
import sqlite3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.common.exceptions import NoSuchElementException

###### WEBDRIVER OPTIONS #####
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
logger = Logger(log_folder=r"Logs/save_performances_data_to_db", std_output=True)
database = Database("Matches_DB_copy.db", logger)


class Match:
    matches = dict()
    logger = logger

    def __init__(self, whoscored_id):
        self.whoscored_id = whoscored_id
        self.type = self.type_of_match()
        self.match_id = f"UCL_{self.whoscored_id}"
        Match.matches[self.match_id] = self     # adding match to the dictionary of all exciting match objects

        self.log(f"Match with ID {self.match_id} created.")

        # getting match data from database
        match_data = self.get_match_data_from_db()
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]

        self.log(f"Data of match {self.match_id} got from database.")

        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id)
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id)

    def delete_match(self):
        Match.log(f"Match with ID {self.match_id} deleted.")
        del self

    def __del__(self):
        Match.matches.pop(self.match_id, None)

    def __str__(self):
        print(50 * "#")
        print(f"MATCH: {self.team_home.team_name} - {self.team_away.team_name}")
        print(f"Season: {self.season}")
        print(f"Date: {self.date}")
        print(f"Centre file: {self.centre_file}")
        print(f"Preview file: {self.preview_file}")
        print(f"Link: {self.link}")
        print(self.team_home)
        print(self.team_away)
        return "#" * 50

    @classmethod
    def create_match(cls, *args, **kwargs):
        """ Function to create match objects.
        :param args: arguments for __init__ method
        :param kwargs: arguments for __init__ method
        """
        return cls(*args, **kwargs)

    @classmethod
    def log(cls, *args, **kwargs):
        if cls.logger:
            logger.write(*args, **kwargs)

    @classmethod
    def delete_all_matches(cls):
        for match_id in list(cls.matches):
            del cls.matches[match_id]

    def type_of_match(self):
        """ Function to define a type of match: UCL match or league match. """
        if len(database.select("UCL_Matches", UCL_Match_WhoScored_ID=self.whoscored_id)) != 0:
            return "UCL_Matches"
        elif len(database.select("Matches", Match_Whoscored_ID=self.whoscored_id)) != 0:
            return "Matches"
        else:
            raise Exception(f"Error! Match with ID {self.whoscored_id} doesn't exist.")

    def get_match_data_from_db(self):
        """ Function getting match data from the database. """
        if self.type == "UCL_Matches":
            return database.select(self.type, UCL_Match_WhoScored_ID=self.whoscored_id)[0]
        elif self.type == "Matches":
            return database.select(self.type, Match_WhoScored_ID=self.whoscored_id)[0]
        else:
            raise Exception("Error! Match with this ID (or this table) doesn't exist.")


class PrevMatch:
    prev_matches = dict()
    logger = logger

    def __init__(self, whoscored_id, ucl_match, team):
        self.whoscored_id = int(whoscored_id)
        self.type = self.type_of_prev_match()
        self.team_ucl = team
        self.team_whoscored_id = team.split("_")[2]
        self.ucl_match = Match.matches[ucl_match]
        self.match_id = f"Prev_{str(self.whoscored_id)}_{ucl_match}"
        PrevMatch.prev_matches[self.match_id] = self  # adding match to the dictionary of all exciting match objects

        self.log(f"PrevMatch with ID {self.match_id} created.")

        # getting match data from database
        match_data = self.get_match_data_from_db()
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]
        self.league = match_data["League"] if self.type == "Matches" else "UCL"

        self.log(f"Data of PrevMatch with ID {self.match_id} got from teh database.")

        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id, prev=True) if match_data["Team_1_ID"] == self.team_whoscored_id else match_data["Team_1_ID"]
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id, prev=True) if match_data["Team_2_ID"] == self.team_whoscored_id else match_data["Team_2_ID"]

    def delete_match(self):
        PrevMatch.log(f"PrevMatch with ID {self.match_id} deleted.")
        del self

    def __del__(self):
        PrevMatch.prev_matches.pop(self.match_id, None)

    def __str__(self):
        print(50 * "=")
        home = self.team_home.team_name if type(self.team_home) != str else self.team_home
        away = self.team_away.team_name if type(self.team_away) != str else self.team_away
        print(f"MATCH: {home} - {away}")
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
    def create_prev_match(cls, *args, **kwargs):
        """ Function to create match objects.
        :param args: arguments for __init__ method
        :param kwargs: arguments for __init__ method
        """
        return cls(*args, **kwargs)

    @classmethod
    def log(cls, *args, **kwargs):
        if cls.logger:
            logger.write(*args, **kwargs)

    @classmethod
    def delete_all_prev_matches(cls):
        for match_id in list(cls.matches):
            del cls.matches[match_id]

    def type_of_prev_match(self):
        """ Function to define a type of match: UCL match or league match. """
        if len(database.select("UCL_Matches", UCL_Match_WhoScored_ID=self.whoscored_id)) != 0:
            return "UCL_Matches"
        elif len(database.select("Matches", Match_Whoscored_ID=self.whoscored_id)) != 0:
            return "Matches"
        else:
            raise Exception(f"Error! Match with ID {self.whoscored_id} doesn't exist.")

    def get_match_data_from_db(self):
        """ Function getting match data from the database. """
        if self.type == "UCL_Matches":
            return database.select(self.type, UCL_Match_WhoScored_ID=self.whoscored_id)[0]
        elif self.type == "Matches":
            return database.select(self.type, Match_WhoScored_ID=self.whoscored_id)[0]
        else:
            raise Exception("Error! Match with this ID (or this table) doesn't exist.")


class Team:
    teams = dict()
    logger = logger
    num_last_matches = 5    # number of last league matches of Team

    def __init__(self, whoscored_id, kind, match_id, prev=False):  # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.prev = prev
        self.main_match = Match.matches[match_id] if prev is False else PrevMatch.prev_matches[match_id]
        self.match_id = match_id
        self.match_whoscored_id = self.main_match.whoscored_id # if prev is False else PrevMatch.prev_matches[self.match_id].whoscored_id
        self.team_id = f"Team_{self.type}_" + str(whoscored_id) + "_" + match_id
        Team.teams[self.team_id] = self

        # getting data about Team from database
        team_data = database.select("Teams", Team_ID=self.whoscored_id)[0]
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]

        self.log(f"Team {self.team_name} in match {self.main_match.match_id} with ID {self.team_id} created.")
        self.log(f"Data of team with ID {self.team_id} got from the database.")

        # getting data about team in match from database or html files
        data = None
        if database.is_element_in_db("Teams_in_" + self.main_match.type, Team_Match_ID=self.team_id):
            data = database.select("Teams_in_" + self.main_match.type, Team_Match_ID=self.team_id)[0]
        self.predicted = self.get_predicted_squad() if data is None else data["Predicted"].split(",")
        self.starting = self.get_lineup() if data is None else data["Starting"].split(",")
        assert len(self.predicted) == 11 and len(self.starting) == 11
        bench = self.get_bench() if data is None else (data["Bench"].split(","), data["Substitutes"].split(")"))
        self.bench = bench[0]
        self.substitutes = bench[1]
        if data is None:
            self.missing = self.get_missing_players()
        else:
            self.missing = {player.split(":")[0]: player.split(":")[1] for player in data["Missing"].split(",")} \
                if data["Missing"] != '' else {}
        self.all_squad = list(set(self.predicted + self.starting + self.bench + list(self.missing.keys())))

        self.log(f"Data about squad of team with ID {self.team_id} got from the database.")

        # getting a few last matches of team and previous performances of players
        if self.prev is False:
            self.prev_matches = self.get_prev_matches()
            if data is None:
                self.save_team_UCL_into_db()
            self.players = {idx: Performance(idx, self.team_id) for idx in self.all_squad}
            for prev_match_id in self.prev_matches:
                PrevMatch.create_prev_match(str(prev_match_id), ucl_match=self.match_id, team=str(self.team_id))
            self.log(f"{self.team_id} -> previous matches: {self.prev_matches}")
            self.log(f"{self.team_id} -> performances of players: {list(self.players.keys())}")
        else: # getting a few last matches of team and previous performances of players
            self.team_ucl = self.main_match.team_ucl
            if data is None:
                self.save_team_into_db()
            self.prev_players = {idx: Prev_Performance(idx, self.team_id, self.team_ucl) for idx in self.all_squad}
            # self.prev_players = self.all_squad
            # self.log(f"{self.team_id} -> previous performances of players: {self.prev_players}")
            self.log(f"{self.team_id} -> previous performances of players: {list(self.prev_players.keys())}")

        self.log(f"Data about previous performances for players of team with ID {self.team_id} got from the database/html files.")

    def delete_match(self):
        Team.log(f"Team with ID {self.team_id} deleted.")
        del self

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
        if self.prev is False:
            print(f"Players: {list(self.players.keys())}")
            print(f"Number of players: {len(list(self.players))}")
            print(f"Prev matches: {self.prev_matches}")
        else:
            print(f"Prev_players: {self.prev_players}")
            print(f"Number of prev_players: {len(list(self.prev_players))}")
        return ""

    @classmethod
    def create_team(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def log(cls, *args, **kwargs):
        if cls.logger:
            logger.write(*args, **kwargs)

    @classmethod
    def delete_all_teams(cls):
        for team_id in list(cls.teams):
            del cls.teams[team_id]

    def save_team_UCL_into_db(self):
        database.insert("Teams_in_UCL_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), ",".join(self.substitutes),
                        ",".join([f"{k}:{v}" for k, v in self.missing.items()]),
                        ",".join(self.prev_matches))  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def save_team_into_db(self):
        miss = ",".join([f"{k}:{v}" for k, v in self.missing.items()]) if len(self.missing.keys()) != 0 else ''
        subs = ",".join(self.substitutes) if len(self.substitutes) != 0 else ''
        database.insert("Teams_in_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), subs, miss)  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def get_predicted_squad(self):
        with open(self.main_match.preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            all_elements = soup.find_all("ul", class_="player")
            all_predicted = []
            for player in all_elements:
                all_predicted.append(player.get('data-playerid'))
            team_preview = all_predicted[:11] if self.type == "home" else all_predicted[11:]
            self.log(f"{self.team_id} -> predicted squad got from html file.")
            return team_preview

    def get_lineup(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(self.main_match.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            pitch_element = soup.find_all("div", class_="pitch-field")
            team_squad = []
            team_elements = pitch_element[num].find_all("div", class_="player")
            for player in team_elements:
                team_squad.append(player.get('data-player-id'))
            self.log(f"{self.team_id} -> line-up got from html file.")
            return team_squad

    def get_bench(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(self.main_match.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            bench_element = soup.find_all("div", class_="substitutes")
            team_bench, team_substitues = list(), list()
            team_elements = bench_element[num].find_all("div", class_="player")
            for player in team_elements:
                team_bench.append(player.get('data-player-id'))
                if player.get('data-subbed-in') == "true":
                    team_substitues.append(player.get('data-player-id'))
            self.log(f"{self.team_id} -> data about players on the bench got from html file.")
            return team_bench, team_substitues

    def get_missing_players(self):
        with open(self.main_match.preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            missing = dict()
            element = soup.find("div", attrs={"id": "missing-players"})
            div_elem = element.find("div", class_=self.type)
            for tr_elem in div_elem.find_all("tr")[1:]:
                try:
                    player_id = tr_elem.find("td", class_="pn").find("a", class_="player-link").get("href").split("/")[2]
                    player_status = tr_elem.find("td", class_="confirmed").string
                except AttributeError:
                    continue
                missing[player_id] = player_status
            self.log(f"{self.team_id} -> data about missing players got from html file.")
            return missing

    def get_prev_matches(self):
        all_prev_matches = [prev_match['Match_WhoScored_ID'] for prev_match
                            in database.select("UCL_Matches_Matches", UCL_Match_WhoScored_ID=self.match_whoscored_id)]
        league_prev_matches = []
        for match in all_prev_matches:
            team_match = database.select("Matches", order_by="Date", option_order="DESC", Match_WhoScored_ID=match)[0]
            league_prev_matches.append(team_match)
        print("league_prev_matches = ", league_prev_matches)
        league_prev_matches = list(filter(lambda game: str(self.whoscored_id) in (game['Team_1_ID'], game['Team_2_ID']), league_prev_matches))

        all_ucl_matches = database.select("UCL_Matches", order_by="Date", option_order="DESC", Season=self.main_match.season)
        team_ucl_matches = list(filter(lambda game: self.whoscored_id in (game['Team_1_ID'], game['Team_2_ID']), all_ucl_matches))
        prev_ucl_matches = list(filter(lambda game: game['Date'] < self.main_match.date, team_ucl_matches))
        prev_matches = list(sorted(league_prev_matches + prev_ucl_matches, key=lambda game: game['Date'], reverse=True))
        result = []
        for prev_match in prev_matches:
            column = "UCL_Match_WhoScored_ID" if 'Champions' in prev_match['Link'] else "Match_WhoScored_ID"
            result.append(str(prev_match[column]))
        return result[:Team.num_last_matches]

    """def get_positions_websites(self):
        pass"""


class Performance:
    players = dict()
    logger = logger

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
    def log(cls, *args, **kwargs):
        if cls.logger:
            logger.write(*args, **kwargs)

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


class Prev_Performance:
    prev_players = dict()
    logger = logger

    def __init__(self, player_id, team_id, ucl_team_id):
        self.prev_team_id = team_id
        self.match_id = Team.teams[self.prev_team_id].match_id
        self.whoscored_id = player_id
        self.team_id = team_id
        self.ucl_team_id = ucl_team_id
        self.ucl_performance_id = Team.teams[self.ucl_team_id].players[self.whoscored_id].performance_id \
            if self.whoscored_id in Team.teams[self.ucl_team_id].players.keys() else None
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
        if not database.is_element_in_db("Prev_Performances", Prev_Performance_ID=self.prev_performance_id):
            self.save_prev_performance_data_into_db()

    def __del__(self):
        Prev_Performance.prev_players.pop(self.prev_performance_id, None)

    def __str__(self):
        print(50 * "-")
        print(f"PLAYER: {self.name} ({self.whoscored_id})")
        print(f"Performance_ID: {self.prev_performance_id}")
        print(f"Link: {self.link}")
        print(f"Starting: {self.starting}")
        print(f"Substitute: {self.substitute}")
        print(f"On bench but no sub: {self.bench_no_sub}")
        print(f"Missing: {self.missing}")
        return "*" * 50

    @classmethod
    def create_prev_performance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def log(cls, *args, **kwargs):
        if cls.logger:
            logger.write(*args, **kwargs)

    @classmethod
    def delete_all_prev_performances(cls):
        for prev_performance_id in list(cls.players):
            del cls.players[prev_performance_id]

    def save_player_data_into_db(self):
        name_player = ''
        for website in (PrevMatch.prev_matches[self.match_id].centre_file, PrevMatch.prev_matches[self.match_id].preview_file):
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
        database.insert("Prev_Performances", True, self.prev_performance_id, self.whoscored_id, self.name,
                        self.ucl_performance_id, self.team_id, self.starting, self.bench_no_sub, self.substitute,
                        self.missing)

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

print("Module classes.py imported.")
test = Match.create_match("458711")
del test
test = Match.create_match("458735")
del test
test = Match.create_match("458740")
del test
database.disconnect()
