# Copyright (c) Jakub Wilczyński 2020
# classes: Match, PrevMatch, Team, Performance, PrevPerformance, Incident, Position

from tools import Database, Logger

from time import sleep, asctime
import datetime
from random import uniform
from bs4 import BeautifulSoup
import sqlite3
from unidecode import unidecode

ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015',
               '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
logger = Logger(log_folder=r"Logs/save_performances_data_to_db", std_output=True)
database = Database("Matches_DB_copy.db", logger)
league_tables = Database("League_Tables.db", logger)


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
        self.duration = self.get_duration()

        self.log(f"Data of match {self.match_id} got from database.")

        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id) \
            if Match.check_team(match_data["Team_1_ID"], match_data["Season"]) else match_data["Team_1_ID"]
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id) \
            if Match.check_team(match_data["Team_2_ID"], match_data["Season"]) else match_data["Team_2_ID"]

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
    def analyze_match(cls, *args, **kwargs):
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

    def get_duration(self):
        minutes = 93
        for kind in "home", "away":
            with open(self.centre_file, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                if len(soup.find_all(lambda tag: "Extra time:" in tag.text)) > 0:
                    minutes = 120
                timeline = soup.find("div", class_="timeline-content")
                timeline_team = timeline.find("div", attrs={"class": "timeline-events", "data-field": kind})
                last_incident = [x for x in timeline_team.find_all("div") if "incident-icon" in x['class']][-1]
                if int(last_incident['data-minute']) >= minutes:
                    minutes = int(last_incident['data-minute']) + 1
        return minutes

    @staticmethod
    def check_team(team_id, ucl_season):
        """ This function answers that the prev matches are available for the current team. Returns True/False."""
        league_name = database.select("Teams", Team_ID=team_id)[0]["League"]
        if league_name in ['England', 'Spain', 'Germany', 'Italy', 'France']:  # TOP 5 leagues - all seasons with available Preview section
            return True
        if league_name in ['Netherlands', 'Russia'] and ucl_season in ALL_SEASONS[3:]:  # NED and RUS - from 2013/2014
            return True
        if league_name == 'Turkey' and ucl_season in ALL_SEASONS[4:]:  # Turkey - from 2014/2015
            return True
        if league_name == 'Portugal' and ucl_season in ALL_SEASONS[-4:]:  # Portugal - from 2016/2017
            return True
        return False


class PrevMatch:
    prev_matches = dict()
    logger = logger

    def __init__(self, whoscored_id, ucl_match, team):
        self.whoscored_id = whoscored_id
        self.type = self.type_of_prev_match()
        self.team_ucl = Team.teams[team]
        self.team_whoscored_id = str(self.team_ucl.whoscored_id)
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
        self.duration = self.get_duration()
        result = self.get_result()
        self.score_home = result[0]
        self.score_away = result[1]

        self.log(f"Data of PrevMatch with ID {self.match_id} got from the database.")
        print("Condition: ", match_data["Team_2_ID"] == self.team_whoscored_id)
        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id, prev=True) if str(match_data["Team_1_ID"]) == self.team_whoscored_id else str(match_data["Team_1_ID"])
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id, prev=True) if str(match_data["Team_2_ID"]) == self.team_whoscored_id else str(match_data["Team_2_ID"])
        self.team = self.team_home if type(self.team_home) == Team else self.team_away
        self.rival = self.team_home if type(self.team_away) == Team else self.team_away
        assert type(self.team) == Team
        league_data = self.get_league_data()
        self.league_diff = league_data["difference"]
        self.ratio_points = league_data["ratio"]

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
        for match_id in list(cls.prev_matches):
            del cls.prev_matches[match_id]

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

    def get_duration(self):
        minutes = 93
        for kind in "home", "away":
            with open(self.centre_file, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                if len(soup.find_all(lambda tag: "Extra time:" in tag.text)) > 0:
                    minutes = 120
                    break
                timeline = soup.find("div", class_="timeline-content")
                timeline_team = timeline.find("div", attrs={"class": "timeline-events", "data-field": kind})
                last_incident = [x for x in timeline_team.find_all("div") if "incident-icon" in x['class']][-1]
                if int(last_incident['data-minute']) >= minutes:
                    minutes = int(last_incident['data-minute']) + 1
        return minutes

    def get_result(self):
        with open(self.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            result = soup.find("td", class_='result').string.replace('*', '').split(":")
            score_home = int(result[0].strip())
            score_away = int(result[1].strip())
        return score_home, score_away

    def get_league_data(self):
        tables = [x['name'] for x in league_tables.select("sqlite_master", type="table")
                  if f"{self.league}_{self.season.replace('/', '_')}_day_" in x['name']]
        dates = [tab.split("_day_")[-1] for tab in tables].append(self.date.replace("-", "_"))
        dates = dates.sort()
        idx = dates.index(self.date.replace("-", "_"))
        table = f"{self.league}_{self.season.replace('/', '_')}_day_{dates[idx-1]}"
        team = league_db.select(table, Team_ID=self.team.whoscored_id)[0]
        rival = league_db.select(table, Team_ID=self.rival)[0]
        best_team = list(sorted(league_db.select(table), key=lambda x: x["Points"]))[-1]
        difference = team["Points"] - best_team["Points"]
        ratio = round((team["Points"]/team["Matches"])/(rival["Points"]/rival["Matches"]), 3) \
            if 0 not in (rival["Points"], rival["Matches"]) else 5.000
        return {"team position": team["Position"], "rival position": rival["Position"],
                "team points": team["Points"], "rival points": rival["Points"],
                "difference": difference, "ratio": ratio}

    @staticmethod
    def check_team(team_id, ucl_season):
        """ This function answers that the prev matches are available for the current team. Returns True/False."""
        league_name = database.select("Teams", Team_ID=team_id)[0]["League"]
        if league_name in ['England', 'Spain', 'Germany', 'Italy', 'France']:  # TOP 5 leagues - all seasons with available Preview section
            return True
        if league_name in ['Netherlands', 'Russia'] and ucl_season in ALL_SEASONS[3:]:  # NED and RUS - from 2013/2014
            return True
        if league_name == 'Turkey' and ucl_season in ALL_SEASONS[4:]:  # Turkey - from 2014/2015
            return True
        if league_name == 'Portugal' and ucl_season in ALL_SEASONS[-4:]:  # Portugal - from 2016/2017
            return True
        return False


class Team:
    teams = dict()
    logger = logger

    def __init__(self, whoscored_id, kind, match_id, prev=False):  # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.prev = prev
        self.match = Match.matches[match_id] if prev is False else PrevMatch.prev_matches[match_id]
        self.match_id = match_id
        self.team_id = f"Team_{self.type}_" + str(whoscored_id) + "_" + match_id
        Team.teams[self.team_id] = self

        # getting data about Team from database
        team_data = database.select("Teams", Team_ID=self.whoscored_id)[0]
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]
        if self.prev:
            self.lost_goals = self.match.score_away if self.type == "home" else self.match.score_home

        self.log(f"Team {self.team_name} in match {self.match.match_id} with ID {self.team_id} created.")
        self.log(f"Data of team with ID {self.team_id} got from the database.")

        # getting data about team in match from database or html files
        data = None
        if database.is_element_in_db("Teams_in_" + self.match.type, Team_Match_ID=self.team_id):
            data = database.select("Teams_in_" + self.match.type, Team_Match_ID=self.team_id)[0]
        self.predicted = self.get_predicted_squad() if data is None else data["Predicted"].split(",")
        self.starting = self.get_lineup() if data is None else data["Starting"].split(",")
        assert len(self.predicted) == 11 and len(self.starting) == 11
        bench = self.get_bench() if data is None else (data["Bench"].split(","), data["Substitutes"].split(","))
        self.bench = bench[0]
        self.substitutes = bench[1]
        if data is None:
            self.missing = self.get_missing_players()
        else:
            self.missing = {player.split(":")[0]: player.split(":")[1] for player in data["Missing"].split(",")} \
                if data["Missing"] != '' else {}
        self.all_squad = list(set(self.predicted + self.starting + self.bench + list(self.missing.keys())))
        self.incidents = self.get_incidents()       # getting incidents in team (goals, cards etc...)
        self.team_news = self.get_team_news() if self.prev is False else None

        self.log(f"Data about squad of team with ID {self.team_id} got from the database.")

        # for instance of Team in UCL match -> getting a few last matches of team and creating performances of players
        if self.prev is False:
            self.prev_matches = self.get_prev_matches() # getting all previous matches for team
            # self.last_matches = {num: prev for num, prev in self.prev_matches.items() if num <= Team.num_last_matches}
            if data is None:
                self.save_team_UCL_into_db()
            for num, prev_match_id in self.prev_matches.copy().items():
                self.prev_matches[num] = PrevMatch(str(prev_match_id), ucl_match=self.match_id, team=str(self.team_id)).team

            self.players = {idx: Performance(idx, self.team_id) for idx in self.all_squad}
            self.log(f"{self.team_id} -> previous matches: {self.prev_matches}")
            self.log(f"{self.team_id} -> performances of players: {list(self.players.keys())}")

        else: # for instance of Team in PrevMatch -> getting a few last matches of team and previous performances of players
            if data is None:
                self.save_team_into_db()
            self.prev_players = {idx: Prev_Performance(idx, self.team_id, self.match.team_ucl.team_id) for idx in self.match.team_ucl.all_squad}
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
        '''if self.prev is False:
            print(f"Players: {list(self.players.keys())}")
            print(f"Number of players: {len(list(self.players))}")
            print(f"Prev matches: {self.prev_matches}")
        else:
            print(f"Prev_players: {self.prev_players}")
            print(f"Number of prev_players: {len(list(self.prev_players))}")'''
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
                        ",".join(self.prev_matches.values()))  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def save_team_into_db(self):
        miss = ",".join([f"{k}:{v}" for k, v in self.missing.items()]) if len(self.missing.keys()) != 0 else ''
        subs = ",".join(self.substitutes) if len(self.substitutes) != 0 else ''
        database.insert("Teams_in_Matches", True, self.team_id, self.whoscored_id, self.type, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), subs, miss)  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def get_predicted_squad(self):
        with open(self.match.preview_file, "r", encoding="utf-8") as file:
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
        with open(self.match.centre_file, "r", encoding="utf-8") as file:
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
        with open(self.match.centre_file, "r", encoding="utf-8") as file:
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
        with open(self.match.preview_file, "r", encoding="utf-8") as file:
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
        all_league_prev_ids = [prev_match['Match_WhoScored_ID'] for prev_match
                               in database.select("UCL_Matches_Matches", UCL_Match_WhoScored_ID=self.match.whoscored_id)]
        league_prev_matches = [database.select("Matches", Match_WhoScored_ID=match_id)[0] for match_id in all_league_prev_ids]
        league_prev_matches = list(filter(lambda m: str(self.whoscored_id) in (m['Team_1_ID'], m['Team_2_ID']), league_prev_matches))

        # probable changes of concept in the future
        """all_ucl_matches = database.select("UCL_Matches", order_by="Date", option_order="DESC", Season=self.match.season)
        team_ucl_matches = list(filter(lambda x: self.whoscored_id in (x['Team_1_ID'], x['Team_2_ID']), all_ucl_matches))
        prev_ucl_matches = list(filter(lambda g: g['Date'] < self.match.date, team_ucl_matches))"""

        prev_matches = list(sorted(league_prev_matches, key=lambda x: x['Date'], reverse=True))
        result = []
        for prev_match in prev_matches:
            column = "UCL_Match_WhoScored_ID" if 'Champions-League' in prev_match['Link'] else "Match_WhoScored_ID"
            result.append(str(prev_match[column]))
        return {key: val for key, val in enumerate(result, start=1)}

    def get_incidents(self):
        with open(self.match.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            timeline = soup.find("div", attrs={"class": "timeline-content"})
            timeline_team = timeline.find("div", attrs={"class": "timeline-events", "data-field": self.type})
            elements = timeline_team.find_all("div", attrs={"data-team-id": str(self.whoscored_id)})
            incidents = []
            for elem in elements:
                if elem["data-type"] in ("34", "40", "7"):  # these incidents are unimportant
                    continue
                try:
                    minute = int(elem["data-minute"])
                    player_id = elem["data-player-id"]
                    name = elem["title"]
                except KeyError:
                    if elem['data-type'] == "17" and elem['data-card-type'] == "31":
                        name = "Yellow Card"
                    else:
                        continue
                incidents.append(Incident(self.team_id, minute, player_id, name))
            return incidents

    def get_team_news(self):
        num = 0 if self.type == "home" else 1
        with open(self.match.preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            teams_news = soup.find("div", attrs={"id": "preview-team-news"})
            try:
                comments = teams_news.find_all("ul", class_="items")[num].find_all("li")
            except AttributeError:
                teams_news = soup.find("div", class_="preview-news-items")
                comments = teams_news.find_all("ul", class_="items")[num].find_all("li")
            news = ' '.join([comment.string for comment in comments])
            print(news)
        return news


class Incident:
    def __init__(self, team_id, minute, player_id, name):
        self.team_id = team_id
        self.minute = minute
        self.player_id = player_id
        self.name = name
        self.check_name()

    def check_name(self):
        types = {'Shot on post', 'Penalty Saved', 'Red Card', 'Sub in', 'Penalty scored', 'Clearance off the line', 'Goal',
                 'Yellow Card', 'Error lead to goal', 'Assist', 'Penalty missed', 'Sub out', 'Own goal'}
        if self.name not in types:
            raise Exception(f"ERROR! Unknown type of incident: {self.name}")


class Performance:
    players = dict()
    logger = logger
    num_last_matches = 5    # number of last league matches of Team

    def __init__(self, player_id, team_id):
        self.whoscored_id = player_id
        self.team_id = team_id
        self.team = Team.teams[team_id]
        self.ucl_match = self.team.match
        self.performance_id = str(self.whoscored_id) + "_" + str(self.ucl_match.whoscored_id)     # Performance ID
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

        self.prev_performances = self.get_prev_performances()
        self.last_performances = {num: prev for num, prev in self.prev_performances.items() if num <= Performance.num_last_matches}

        # features
        self.missing = self.is_missing()
        self.feature_starting_in_prev_matches()
        self.season_minutes, self.season_percentage, self.last_minutes, self.last_percentage = self.feature_minutes()
        self.in_team_news = 1 if self.name in self.team.team_news or unidecode(self.name) in self.team.team_news else 0
        self.features_league_tables()
        self.feature_missing_in_prev_matches()
        self.feature_ratings_in_prev_matches()

        # saving all data about this performance into database
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
        for website in (self.ucl_match.centre_file, self.ucl_match.preview_file):
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
                f"Error! Name of player with ID {self.whoscored_id} for match {self.ucl_match.whoscored_id} not downloaded...")
        database.insert("Players", True, self.whoscored_id, player_name,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")

    def save_performance_data_into_db(self):
        """update needed"""
        if not database.is_element_in_db("Performances", Performance_ID=self.performance_id):
            database.insert("Performances", True, self.performance_id, self.whoscored_id, self.name, self.team_id,
                            self.predicted, self.starting, self.bench_no_sub, self.substitute, self.missing,
                            self.prev_1_start, self.prev_2_start, self.prev_3_start, self.prev_4_start, self.prev_5_start,
                            self.prev_1_missing, self.prev_2_missing, self.prev_3_missing, self.prev_4_missing,
                            self.prev_5_missing, self.prev_1_rating, self.prev_2_rating, self.prev_3_rating, 
                            self.prev_4_rating, self.prev_5_rating, self.season_percentage, self.in_team_news)

    def is_missing(self):
        status = ''
        for p_id, value in Team.teams[self.team_id].missing.items():
            if p_id == self.whoscored_id:
                status = value
        level = {'': 0, 'Doubtful': 1, 'Out': 2}
        if status not in level:
            raise Exception(f'Error! Unknown status "{status}"of missing player {self.whoscored_id} in {self.ucl_match.whoscored_id}')
        return level[status]

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

    def get_prev_performances(self):
        prev_performances = dict()
        for num, prev_match_team in self.team.prev_matches.items():
            prev_performance_id = f"Prev_{self.whoscored_id}_{prev_match_team.team_id}"
            if database.is_element_in_db("Prev_Performances", Prev_Performance_ID=prev_performance_id):
                prev_perf = database.select("Prev_Performances", Prev_Performance_ID=prev_performance_id)[0]
                prev_performances[num] = prev_perf
            else:
                raise Exception(f"Error! Prev_Performance for performance {prev_performance_id} not found in the database!")
        return prev_performances

    def feature_starting_and_missing_in_prev_matches(self):
        for num, last_perf in self.last_performances.items():
            exec(f'self.prev_{num}_start = int({last_perf["Starting"]})')
            exec(f'self.prev_{num}_missing = int({last_perf["Missing"]})')

    def feature_minutes(self):
        """ This function calculates the sum of played minutes in the all current season for the player and
        percentage of possible minutes. The same for few last matches."""
        season_player_minutes, season_matches_minutes, last_player_minutes, last_matches_minutes = 0, 0, 0, 0
        for num, prev_performance in self.prev_performances.items():
            if prev_performance.missing == 0:
                season_matches_minutes += int(prev_performance["Duration_of_match"])
            season_player_minutes += int(prev_performance["Played_minutes"])
            if num <= Performance.num_last_matches:
                if prev_performance.missing == 0:
                    last_matches_minutes += int(prev_performance["Duration_of_match"])
                last_player_minutes += int(prev_performance["Played_minutes"])
        if season_matches_minutes == 0:
            last_matches_minutes = season_matches_minutes = 1
        return (season_player_minutes, round(season_player_minutes/season_matches_minutes, 3),
                last_player_minutes, round(last_player_minutes/last_matches_minutes, 3))

    def features_league_tables(self):
        for num, prev_performance in self.prev_performances.items():
            exec(f"self.prev_{num}_diff_points = prev_performance.prev_match.league_diff")
            exec(f"self.prev_{num}_ratio_points = prev_performance.prev_match.ratio_points")

    def feature_missing_in_prev_matches(self):
        for num, prev_performance in self.prev_performances.items():
            exec(f"self.prev_{num}_missing = prev_performance.prev_match['Missing']")

    def feature_ratings_in_prev_matches(self):
        for num, prev_performance in self.prev_performances.items():
            exec(f"self.prev_{num}_rating = prev_performance['Rating']")


class Prev_Performance:
    prev_players = dict()
    logger = logger

    def __init__(self, player_id, team_id, ucl_team_id):
        self.whoscored_id = player_id
        self.team_id = team_id
        self.team = Team.teams[team_id]
        self.prev_match = self.team.match
        self.ucl_team_id = ucl_team_id
        self.ucl_match_id = ucl_team_id.split("_")[-1]
        self.ucl_performance_id = f"{player_id}_{self.ucl_match_id}"
        self.prev_performance_id = "Prev_" + str(self.whoscored_id) + "_" + str(self.team_id)
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

        self.incidents = [incident for incident in self.team.incidents if incident.player_id == self.whoscored_id]
        self.play_data = self.analyze_incidents()
        self.duration_of_match = self.prev_match.duration
        self.played_minutes = self.get_played_minutes()
        self.rating = self.get_rating()

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
        for prev_performance_id in list(cls.prev_players):
            del cls.prev_players[prev_performance_id]

    def save_player_data_into_db(self):
        name_player = ' '
        for website in (self.team.match.ucl_match.centre_file, self.team.match.ucl_match.centre_file):
            with open(website, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                player_div = soup.find("div", attrs={"class": "player", "data-player-id": self.whoscored_id})
                if player_div is not None:
                    name_player = player_div.find("div", attrs={"class": "player-name-wrapper"})['title']
                    break
                player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": self.whoscored_id})
                if player_ul is not None:
                    name_player = player_ul['title'].split("(")[0]
                for player_miss in soup.find_all("a", class_="player-link"):
                    if str(self.whoscored_id) in player_miss['href']:
                        name_player = player_miss.string
        database.insert("Players", True, self.whoscored_id, name_player,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")

    def save_prev_performance_data_into_db(self):
        """update needed"""
        database.insert("Prev_Performances", True, self.prev_performance_id, self.whoscored_id, self.name,
                        self.ucl_performance_id, self.team_id, self.starting, self.bench_no_sub, self.substitute,
                        self.missing, self.duration_of_match, self.played_minutes, self.rating)

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
            raise Exception(f"Error! Unknown status of missing player {self.whoscored_id} in {self.prev_match.whoscored_id}")

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

    def analyze_incidents(self):
        data = {'sub out': None, 'sub in': None, 'goals': 0, 'assists': 0, 'own goal': 0, 'errors': 0, 'bonuses': 0,
                'yellow card': 0, 'red card': None, 'clean sheet': 1 if self.team.lost_goals == 0 else 0}
        data['bonuses'] = 1 if data['clean sheet'] == 1 else 0
        for incident in self.incidents:
            if incident.name == "Sub out":
                data['sub out'] = incident
            elif incident.name == "Sub in":
                data['sub in'] = incident
            elif incident.name in ("Goal", "Penalty scored"):
                data['goals'] += 1
            elif incident.name == "Assist":
                data['assists'] += 1
            elif incident.name in ("Own goal", "Error lead to goal", "Penalty missed"):
                data['errors'] += 1
            elif incident.name in ("Shot on post", "Clearance off the line", "Penalty saved"):
                data['bonuses'] += 1
            elif incident.name == 'Red Card':
                data['red card'] = incident
                data['errors'] += 1
            elif incident.name == 'Yellow card':
                data['yellow card'] += 1
                data['errors'] += 1
        if self.substitute == 1:
            assert self.substitute == 1 and data["sub in"] is not None
        return data

    def get_played_minutes(self):
        if self.starting == 1:
            if self.play_data['red card'] is not None:
                played_minutes = self.play_data['red card'].minute
            elif self.play_data['sub out'] is not None:
                played_minutes = int(self.play_data['sub out'].minute)
            else:
                played_minutes = self.duration_of_match
        elif self.substitute == 1:
            if self.play_data['red card'] is not None:
                played_minutes = self.play_data['red card'].minute - self.play_data['sub in'].minute
            elif self.play_data['sub out'] is not None:
                played_minutes = self.play_data['sub out'].minute - self.play_data['sub in'].minute
            else:
                played_minutes = self.duration_of_match - self.play_data['sub in'].minute
        else:
            played_minutes = 0
        return played_minutes

    def get_rating(self):
        with open(self.prev_match.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            if self.starting == 1: 
                pitch_element = soup.find_all("div", attrs={'class': 'pitch-field', 'data-field': self.team.type})
                player_elem = pitch_element.find("div", attrs={'class': 'player', 'data-player-id': self.whoscored_id})
                rating = float(player_element.find("span", class_='player-stat-value').string)
            elif self.substitute == 1:
                bench_element = soup.find("div", attrs={'class': 'substitutes', 'data-field': self.team.type})
                player_elem = bench_element.find("div", attrs={'class': 'player', 'data-player-id': self.whoscored_id})
                rating = float(player_element.find("span", class_='player-stat-value').string)
            else:
                rating = 0
        return rating

class Position:
    all_position = []

    def __init__(self, acronym):
        self.acronym = acronym
        self.position = self.set_position()
        self.position_class = self.set_position_class()

    def set_position(self):
        pass

    def set_position_class(self):
        pass


for game in database.select("UCL_Matches", order_by="Date"):
    test = Match.analyze_match(game)
    logger.write(f"Match with ID {game} analyzed.")
    Match.delete_all_matches()
    PrevMatch.delete_all_prev_matches()
    Team.delete_all_teams()
    Performance.delete_all_performances()
    Prev_Performance.delete_all_prev_performances()
database.disconnect()
