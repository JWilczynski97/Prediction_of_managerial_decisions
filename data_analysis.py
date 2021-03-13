# Copyright (c) Jakub Wilczyński 2020
# classes: Match, PrevMatch, Team, Performance, PrevPerformance, Incident

from tools import Database, Logger

from time import sleep, asctime
import datetime
import logging
from statistics import mean
from random import uniform
from bs4 import BeautifulSoup
import sqlite3
from unidecode import unidecode

ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015',
               '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
logger = Logger(log_folder=r"Logs/save_performances_data_to_db", std_output=True)
database = Database("Matches_DB.db", logger)
league_tables = Database("League_Tables.db", logger)

class Match:
    matches = dict()
    logger = logger

    def __init__(self, whoscored_id):
        self.whoscored_id = whoscored_id
        self.type = self.type_of_match()
        self.match_id = f"UCL_{self.whoscored_id}"
        Match.matches[self.match_id] = self     # adding match to the dictionary of all exciting match objects

        self.log(f"-> Analysis of Match with ID {self.match_id}...")

        # getting match data from database
        match_data = self.get_match_data_from_db()
        self.match_id_in_database = match_data["UCL_Match_ID"]
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]

        self.log(f"Data of match {self.match_id} got from database.")

        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id) \
            if Match.check_team(match_data["Team_1_ID"], match_data["Season"]) else match_data["Team_1_ID"]
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id) \
            if Match.check_team(match_data["Team_2_ID"], match_data["Season"]) else match_data["Team_2_ID"]

        self.log(f"-> Analysis of Match with ID {self.match_id} completed.")

    def delete_match(self):
        Match.log(f"Match with ID {self.match_id} deleted.")
        del self

    def __del__(self):
        Match.matches.pop(self.match_id, None)

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
        if database.is_element_in_db("UCL_Matches", UCL_Match_WhoScored_ID=self.whoscored_id):
            return "UCL_Matches"
        elif database.is_element_in_db("Matches", Match_Whoscored_ID=self.whoscored_id):
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

    @staticmethod
    def is_already_analyzed(id_match):
        return id_match in [match['Performance_ID'].split("_")[-1] for match in database.select("Performances")]


class PrevMatch:
    prev_matches = dict()
    logger = logger

    def __init__(self, prev_match_id, ucl_match, team, competition="league"):
        self.whoscored_id = prev_match_id
        self.type = self.type_of_prev_match()
        self.comp = competition
        self.team_ucl = Team.teams[team]
        self.team_whoscored_id = str(self.team_ucl.whoscored_id)
        self.ucl_match = Match.matches[ucl_match]
        self.match_id = f"Prev_{str(self.whoscored_id)}_{ucl_match}" if self.comp != "ucl" else f"Prev_UCL_{str(self.whoscored_id)}_{ucl_match}"
        PrevMatch.prev_matches[self.match_id] = self  # adding match to the dictionary of all exciting match objects
        self.log(f"->  Analysis of PrevMatch with ID {self.match_id}...")

        # getting match data from database
        match_data = self.get_match_data_from_db()
        self.season = match_data["Season"]
        self.date = match_data["Date"]
        self.centre_file = match_data["Centre_file"]
        self.preview_file = match_data["Preview_file"]
        self.link = match_data["Link"]
        self.league = match_data["League"] if self.type == "Matches" else "UCL"
        self.duration = self.get_duration()

        self.log(f"Data of PrevMatch with ID {self.match_id} got from the database.")

        self.team_id = match_data["Team_1_ID"] if int(self.team_ucl.whoscored_id) == int(match_data["Team_1_ID"]) else int(match_data["Team_2_ID"])
        self.rival_id = match_data["Team_1_ID"] if int(self.team_id) == int(match_data["Team_2_ID"]) else int(match_data["Team_2_ID"])

        league_data = self.get_league_data() if self.comp == "league" else 0
        self.league_diff_best = league_data["diff best"] if league_data != 0 else 200
        self.league_diff_rival = league_data["diff rival"] if league_data != 0 else 200

        # creating of team objects (depending of the match type)
        self.team_home = Team(match_data["Team_1_ID"], "home", self.match_id, prev=True) if str(match_data["Team_1_ID"]) == self.team_whoscored_id else str(match_data["Team_1_ID"])
        self.team_away = Team(match_data["Team_2_ID"], "away", self.match_id, prev=True) if str(match_data["Team_2_ID"]) == self.team_whoscored_id else str(match_data["Team_2_ID"])
        self.team = self.team_home if type(self.team_home) == Team else self.team_away
        self.rival = self.team_home if type(self.team_away) == Team else self.team_away

        self.log(f"->  Analysis of PrevMatch with ID {self.match_id} completed.")

    def delete_match(self):
        PrevMatch.log(f"PrevMatch with ID {self.match_id} deleted.")
        del self

    def __del__(self):
        PrevMatch.prev_matches.pop(self.match_id, None)

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

    def get_league_data(self):
        tables = [x['name'] for x in league_tables.select("sqlite_master", type="table")
                  if f"{self.league}_{self.season.replace('/', '_')}_day_" in x['name']]
        dates = [tab.split("_day_")[-1] for tab in tables]
        if self.date.replace("-", "_") not in dates:
            dates += [self.date.replace("-", "_")]
        dates.sort()
        idx = dates.index(self.date.replace("-", "_"))
        table = f"{self.league}_{self.season.replace('/', '_')}_day_{dates[idx-1]}"

        team = league_tables.select(table, Team_ID=int(self.team_id))[0]
        rival = league_tables.select(table, Team_ID=int(self.rival_id))[0]
        rival_diff = team["Points"] - rival["Points"]
        best_team = list(sorted(league_tables.select(table), key=lambda x: x["Points"]))[-1]
        best_diff = team["Points"] - best_team["Points"]
        return {"team position": team["Position"], "rival position": rival["Position"],
                "team points": team["Points"], "rival points": rival["Points"],
                "diff best": best_diff, "diff rival": rival_diff}


class Team:
    teams = dict()
    logger = logger

    def __init__(self, whoscored_id, kind, match_id, prev=False):  # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.prev = prev

        self.match = PrevMatch.prev_matches[match_id] if self.prev is True else Match.matches[match_id]
        self.match_id = match_id

        self.team_id = (f"Team_{self.type}_" + str(whoscored_id) + "_" + match_id)
        if self.prev:
            self.team_id = "_".join(self.team_id.split("_")[:-2])

        Team.teams[self.team_id] = self

        # getting data about Team from database
        team_data = database.select("Teams", Team_ID=self.whoscored_id)[0]
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]

        self.log(f"-->  Team {self.team_name} in match {self.match.match_id} with ID {self.team_id} is creating...")
        self.log(f"Data of team with ID {self.team_id} got from the database.")

        # getting data about team in match from database or html files
        table = "Teams_in_UCL_Matches" if self.prev is False else "Teams_in_Matches"
        data = database.select(table, Team_Match_ID=self.team_id)[0] \
            if database.is_element_in_db(table, Team_Match_ID=self.team_id) else None
        self.predicted = self.get_predicted_squad() if data is None else data["Predicted"].split(",")
        self.starting = self.get_lineup() if data is None else data["Starting"].split(",")
        try:
            assert len(self.predicted) == 11 and len(self.starting) == 11
        except AssertionError as e:
            logger.write(f"Team -> {self.team_id} -> AssertionError len(self.predicted) == 11 and len(self.starting) == 11. Content: {e}", level=logging.ERROR)
            logger.write(f"predicted: {len(self.predicted)}\nstarting: {len(self.starting)}")
            logger.write(50*"-")
        bench = self.get_bench() if data is None else (data["Bench"].split(","), data["Substitutes"].split(","))
        self.bench = bench[0]
        self.substitutes = bench[1]
        if data is None:
            self.missing = self.get_missing_players()
        else:
            self.missing = {player.split(":")[0]: player.split(":")[1] for player in data["Missing"].split(",")} \
                if data["Missing"] != '' else {}
        self.all_squad = list(set(self.predicted + self.starting + self.bench + list(self.missing.keys())))
        self.incidents = self.get_incidents()  # getting incidents in team (goals, cards etc...)
        self.team_news = self.get_team_news() if self.prev is False else None

        self.log(f"Data about squad of team with ID {self.team_id} got from the database.")

        # for instance of Team in UCL match -> getting a few last matches of team and creating performances of players
        if self.prev is False:
            for id_player in self.all_squad:
                self.save_player_data_into_db(id_player)
            self.prev_matches, self.prev_ucl_matches = self.get_prev_matches() # getting all previous matches for team
            # self.last_matches = {num: prev for num, prev in self.prev_matches.items() if num <= Team.num_last_matches}
            if data is None:
                self.save_team_UCL_into_db()
            for num, prev_match_id in self.prev_matches.copy().items():
                self.prev_matches[num] = PrevMatch(str(prev_match_id), ucl_match=self.match_id, team=str(self.team_id), competition='league').team
            for num, prev_ucl_match_id in self.prev_ucl_matches.copy().items():
                self.prev_ucl_matches[num] = PrevMatch(str(prev_ucl_match_id), ucl_match=self.match_id, team=str(self.team_id), competition='ucl').team
            self.log(f"Previous matches analyzed: {[x.whoscored_id for x in self.prev_matches.values() if x]}")
            self.log(f"All players: {self.all_squad}")
            self.players = {idx: Performance(idx, self.team_id) for idx in self.all_squad}
            
        else: # for instance of Team in PrevMatch -> getting a few last matches of team and previous performances of players
            if data is None:
                self.save_team_into_db()
            self.prev_players = {idx: Prev_Performance(idx, self.team_id, self.match.team_ucl.team_id) for idx in self.match.team_ucl.all_squad}
            self.log(f"Previous performances for players of team {self.team_id} analyzed.")
        self.log(f"--> Analysis of team {self.team_id} complete.")

    def delete_match(self):
        Team.log(f"Team with ID {self.team_id} deleted.")
        del self

    def __del__(self):
        Team.teams.pop(self.team_id, None)

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
        database.insert("Teams_in_UCL_Matches", False, self.team_id, self.whoscored_id, self.match.date, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), ",".join(self.substitutes),
                        ",".join([f"{k}:{v}" for k, v in self.missing.items()]),
                        ",".join(self.prev_matches.values()), ",".join(self.prev_ucl_matches.values()))  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def save_team_into_db(self):
        miss = ",".join([f"{k}:{v}" for k, v in self.missing.items()]) if len(self.missing.keys()) != 0 else ''
        subs = ",".join(self.substitutes) if len(self.substitutes) != 0 else ''
        database.insert("Teams_in_Matches", False, self.team_id, self.whoscored_id, self.match.date, self.match_id,
                        ",".join(self.all_squad), ",".join(self.predicted), ",".join(self.starting),
                        ",".join(self.bench), subs, miss)  # (...)
        self.log(f"Data about team {self.team_id} saved into the database.")

    def get_predicted_squad(self):
        with open(self.match.preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            pitch = soup.find("div", attrs={'id': 'preview'})
            team_pitch = pitch.find_all("div", class_=self.type)[1]
            all_elements = team_pitch.find_all("ul", class_="player")
            predicted = []
            for player in all_elements:
                predicted.append(player.get('data-playerid'))
            self.log(f"Predicted squad got from html file.")
            return predicted

    def get_lineup(self):
        num = 0 if self.type == "home" else 1  # 1 if type == "away"
        with open(self.match.centre_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            pitch_element = soup.find_all("div", class_="pitch-field")
            team_squad = []
            team_elements = pitch_element[num].find_all("div", class_="player")
            for player in team_elements:
                team_squad.append(player.get('data-player-id'))
            self.log(f"Line-up of team {self.team_id} got from html file.")
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
            self.log(f"Data about substitues of team {self.team_id} got from html file.")
            return team_bench, team_substitues

    def get_missing_players(self):
        with open(self.match.preview_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            missing = dict()
            element = soup.find("div", attrs={"id": "missing-players"})
            if element is None:
                return {}
            div_elem = element.find("div", class_=self.type)
            for tr_elem in div_elem.find_all("tr")[1:]:
                try:
                    player_id = tr_elem.find("td", class_="pn").find("a", class_="player-link").get("href").split("/")[2]
                    player_status = tr_elem.find("td", class_="confirmed").string
                except AttributeError:
                    continue
                missing[player_id] = player_status
            self.log(f"Data about missing players of team {self.team_id} got from html file.")
            return missing

    def save_player_data_into_db(self, id_player):
        if not database.is_element_in_db("Players", Player_WhoScored_ID=id_player):
            player_name = ''
            for website in (self.match.centre_file, self.match.preview_file):
                with open(website, "r", encoding="utf-8") as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                    player_div = soup.find("div", attrs={"class": "player", "data-player-id": id_player})
                    player_div = soup.find("div", attrs={"class": "player is-man-of-the-match", "data-player-id": id_player}) \
                        if player_div is None else player_div
                    if player_div is not None:
                        player_info = player_div.find("div", class_="player-info")
                        player_name = player_info.find("div", attrs={"class": "player-name-wrapper"})['title']
                        break
                    player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": id_player})
                    if player_ul is not None:
                        player_name = player_ul['title'].split("(")[0]
                        break
                    div_missing = soup.find("div", id="missing-players")
                    if div_missing is None:
                        continue
                    missing = div_missing.find_all("a", class_="player-link")
                    for player_miss in missing:
                        if str(id_player) in player_miss['href']:
                            player_name = player_miss.string
            if player_name == '':
                raise Exception(
                    f"Error! Name of player with ID {id_player} for team {self.team_id} not downloaded...")
            database.insert("Players", False, id_player, player_name,
                            f"www.whoscored.com/Players/{id_player}/")
            self.log(f"Data about player {player_name} ({id_player}) saved into database.")

    def get_prev_matches(self):
        all_league_prev_ids = [prev_match['Match_WhoScored_ID'] for prev_match
                               in database.select("UCL_Matches_Matches", UCL_Match_WhoScored_ID=self.match.whoscored_id)]
        league_prev_matches = [database.select("Matches", Match_WhoScored_ID=match_id)[0] for match_id in all_league_prev_ids]
        league_prev_matches = list(filter(lambda m: str(self.whoscored_id) in (m['Team_1_ID'], m['Team_2_ID']), league_prev_matches))
        prev_league = list(sorted(league_prev_matches, key=lambda x: x['Date'], reverse=True))
        prev_league = [str(prev_match["Match_WhoScored_ID"]) for prev_match in prev_league]

        all_ucl_matches = database.select("UCL_Matches", order_by="Date", option_order="DESC", Season=self.match.season)
        team_ucl_matches = list(filter(lambda x: self.whoscored_id in (x['Team_1_ID'], x['Team_2_ID']), all_ucl_matches))
        prev_ucl_matches = list(filter(lambda g: g['Date'] < self.match.date, team_ucl_matches))
        prev_ucl_matches = list(sorted(prev_ucl_matches, key=lambda x: x['Date'], reverse=True))
        prev_ucl = [str(prev_match["UCL_Match_WhoScored_ID"]) for prev_match in prev_ucl_matches]

        previous_league_matches = {key: val for key, val in enumerate(prev_league, start=1)}
        previous_ucl_matches = {key: val for key, val in enumerate(prev_ucl, start=1)}
        self.log(f"Previous matches of team {self.team_id} got from database.")
        return previous_league_matches, previous_ucl_matches

    def choose_most_important_match(self):
        league_prev_matches = {num: prev.match.league_diff_rival for num, prev in self.prev_matches.items() if num != 0}
        min_diff, choice = 100, 0
        for num, rival_diff in league_prev_matches.items():
            if rival_diff < min_diff:
                min_diff = rival_diff
                choice = num
        self.log(f"Previous UCL match not exists, data about previous match number {choice} got.")
        return self.prev_matches[choice]

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
                    if 'yellow card' not in elem:
                        logger.write(f"KeyError in Team.get_incidents()) in element: {elem}")
                    continue
                incidents.append(Incident(self.team_id, minute, player_id, name))
            self.log(f"Data about incidents of team {self.team_id} got from html file.")
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
        self.log(f"Team news section of team {self.team_id} got from html file.")
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

        self.log(f"---->  Performance of player {self.performance_id} is analysing...") 

        data = database.select("Players", Player_WhoScored_ID=self.whoscored_id)[0]

        self.name = data["Name"]
        self.link = data["Link"]

        self.predicted = 1 if self.in_predicted_squad() else 0
        self.starting = 1 if self.in_lineup() else 0

        self.prev_performances, self.prev_ucl_performances = self.get_prev_performances()
        self.last_performances = {num: prev for num, prev in self.prev_performances.items() if num <= Performance.num_last_matches and num != 0}
        self.last_ucl_performance = self.prev_ucl_performances[1]
        self.log(f"Data about player and his previous performances got from database.")

        # features
        self.missing = self.is_missing()
        self.feature_starting_and_missing_in_prev_matches()
        self.season_percentage = self.feature_minutes()
        self.in_team_news = 1 if self.name in self.team.team_news or unidecode(self.name) in self.team.team_news else 0
        # self.feature_missing_in_prev_matches()
        self.feature_ratings_in_prev_matches()
        self.feature_stats_prev_matches()

        # saving all data about this performance into database
        self.save_performance_data_into_db()
        self.log(f"----> Analysis of performance {self.performance_id} completed. Data saved into database.")

    def __del__(self):
        Performance.players.pop(self.performance_id, None)

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

    def save_performance_data_into_db(self):
        """update needed"""
        if not database.is_element_in_db("Performances", Performance_ID=self.performance_id):
            database.insert("Performances", False, self.performance_id, self.name, self.team_id, self.ucl_match.season,
                            self.prev_1_start, self.prev_1_missing, self.prev_1_rating, self.prev_1_diff_rival,
                            self.prev_1_diff_best, self.prev_2_start, self.prev_2_missing, self.prev_2_rating, self.prev_2_diff_rival,
                            self.prev_2_diff_best, self.prev_3_start, self.prev_3_missing, self.prev_3_rating, self.prev_3_diff_rival,
                            self.prev_3_diff_best, self.prev_4_start, self.prev_4_missing, self.prev_4_rating, self.prev_4_diff_rival,
                            self.prev_4_diff_best, self.prev_5_start, self.prev_5_missing, self.prev_5_rating, self.prev_5_diff_rival,
                            self.prev_5_diff_best, self.prev_ucl_start, self.prev_ucl_missing, self.prev_ucl_rating,
                            self.missing, self.predicted, self.season_percentage, self.in_team_news, self.starting)

    def is_missing(self):
        status = ''
        for p_id, value in Team.teams[self.team_id].missing.items():
            if p_id == self.whoscored_id:
                status = value
        level = {'': 0, 'Doubtful': 1, 'Out': 2}
        if status not in level:
            raise Exception(f'Error! Unknown status "{status}" of missing player {self.whoscored_id} in {self.ucl_match.whoscored_id}')
        return level[status]

    def in_predicted_squad(self):
        if self.whoscored_id in Team.teams[self.team_id].predicted:
            return True
        return False

    def in_lineup(self):
        if self.whoscored_id in Team.teams[self.team_id].starting:
            return True
        return False

    def get_prev_performances(self):
        prev_performances, prev_ucl_performances = dict(), dict()
        for num, prev_match_team in self.team.prev_matches.items():
            prev_performance_id = f"Prev_{self.whoscored_id}_{prev_match_team.team_id}"
            if database.is_element_in_db("Prev_Performances", Prev_Performance_ID=prev_performance_id):
                prev_perf = database.select("Prev_Performances", Prev_Performance_ID=prev_performance_id)[0]
                prev_performances[num] = prev_perf
            else:
                raise Exception(f"Error! Prev_Performance for performance {prev_performance_id} not found in the database!")
        for num, prev_match_team in self.team.prev_ucl_matches.items():
            prev_performance_id = f"Prev_{self.whoscored_id}_{prev_match_team.team_id}"
            if database.is_element_in_db("Prev_Performances", Prev_Performance_ID=prev_performance_id):
                prev_perf = database.select("Prev_Performances", Prev_Performance_ID=prev_performance_id)[0]
                prev_ucl_performances[num] = prev_perf
            else:
                raise Exception(f"Error! Prev_Performance for performance {prev_performance_id} not found in the database!")
        return prev_performances, prev_ucl_performances

    def feature_starting_and_missing_in_prev_matches(self):
        for num, last_perf in self.last_performances.items():
            exec(f'self.prev_{num}_start = int({last_perf["Starting"]})')
            exec(f'self.prev_{num}_missing = int({last_perf["Missing"]})')
        exec(f'self.prev_ucl_start = self.last_ucl_performance["Starting"]')
        exec(f'self.prev_ucl_missing = self.last_ucl_performance["Missing"]')
        # no all last matches for first ucl matches of season -> values 99 for p
        for num in range(1, Performance.num_last_matches + 1):
            try:
                exec(f"a = self.prev_{num}_start")
            except AttributeError:
                exec(f'self.prev_{num}_start = 99')
                exec(f'self.prev_{num}_missing = 99')
                exec(f"self.prev_{num}_rating = 99")
                exec(f"self.prev_{num}_diff_rival = 99")
                exec(f"self.prev_{num}_diff_best = 99")

    def feature_minutes(self):
        """ This function calculates the sum of played minutes in the all current season for the player and
        percentage of possible minutes. The same for few last matches."""
        player_minutes, matches_minutes = 0, 0
        for num, prev_performance in self.prev_performances.items():
            if int(prev_performance['Missing']) == 0:
                matches_minutes += int(prev_performance["Duration_of_match"])
            else:
                if int(prev_performance["Played_minutes"]) > 0:
                    matches_minutes += int(prev_performance["Duration_of_match"])
            player_minutes += int(prev_performance["Played_minutes"])
        for num, prev_performance in self.prev_ucl_performances.items():
            if int(prev_performance['Missing']) == 0:
                matches_minutes += int(prev_performance["Duration_of_match"])
            else:
                if int(prev_performance["Played_minutes"]) > 0:
                    matches_minutes += int(prev_performance["Duration_of_match"])
            player_minutes += int(prev_performance["Played_minutes"])
        if matches_minutes == 0:
            assert player_minutes == 0
            matches_minutes = 1
        minutes_percentage = round(player_minutes/matches_minutes, 3)
        assert 0 <= minutes_percentage <= 1.000
        return minutes_percentage

    def feature_ratings_in_prev_matches(self):
        all_ratings = {num: match['Rating'] for num, match in self.last_performances.items() if num != 0}
        for num, prev_rating in all_ratings.items():
            exec(f"self.prev_{num}_rating = prev_rating")
        zeros = [num for num, rat in all_ratings.items() if rat == 0]
        if len(zeros) in (4, 5) or len(zeros) == len(all_ratings):  # default ratings inplace zero-ratings
            for num in zeros:
                exec(f"self.prev_{num}_rating = 5.0")
        elif len(zeros) in (1, 2, 3):                   # average of other ratings inplace zero-ratings
            avg = float(round(mean([rat for num, rat in all_ratings.items() if rat != 0]), 1))
            assert type(avg) is float and avg > 0
            for num in zeros:
                exec(f"self.prev_{num}_rating = avg")
        if self.last_ucl_performance['Rating'] != 0:
            exec(f"self.prev_ucl_rating = self.last_ucl_performance['Rating']")
        else:
            exec(f"self.prev_ucl_rating = round(mean({(self.prev_1_rating, self.prev_2_rating, self.prev_3_rating, self.prev_4_rating, self.prev_5_rating)}), 1)")

    def feature_stats_prev_matches(self):
        for num, prev_performance in self.last_performances.items():
            exec(f"self.prev_{num}_diff_rival = prev_performance['Diff_rival']")
            exec(f"self.prev_{num}_diff_best = prev_performance['Diff_best']")


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

        self.log(f"--->  Previous performance of player {self.prev_performance_id} is analysing...") 

        if not database.is_element_in_db("Players", Player_WhoScored_ID=self.whoscored_id):
            self.save_player_data_into_db()

        if not database.is_element_in_db("Prev_Performances", Prev_Performance_ID=self.prev_performance_id):
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
            self.diff_best = self.prev_match.league_diff_best
            self.diff_rival = self.prev_match.league_diff_rival
            self.save_prev_performance_data_into_db()
        else:
            self.get_data_from_db()
        self.log(f"--->  Analysis of previous performance {self.prev_performance_id} completed.") 

    def __del__(self):
        Prev_Performance.prev_players.pop(self.prev_performance_id, None)

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
        player_name = ''
        for website in (self.prev_match.centre_file, self.prev_match.preview_file):
            with open(website, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                player_div = soup.find("div", attrs={"class": "player", "data-player-id": self.whoscored_id})
                player_div = soup.find("div", attrs={"class": "player is-man-of-the-match", "data-player-id": self.whoscored_id}) \
                    if player_div is None else player_div
                if player_div is not None:
                    player_info = player_div.find("div", class_="player-info")
                    player_name = player_info.find("div", attrs={"class": "player-name-wrapper"})['title']
                    break
                player_ul = soup.find("ul", attrs={"class": "player", "data-playerid": self.whoscored_id})
                if player_ul is not None:
                    player_name = player_ul['title'].split("(")[0]
                    break
                div_missing = soup.find("div", id="missing-players")
                if div_missing is None:
                    continue
                missing = div_missing.find_all("a", class_="player-link")
                for player_miss in missing:
                    if str(self.whoscored_id) in player_miss['href']:
                        player_name = player_miss.string
        if player_name == '':
            raise Exception(
                f"Error! Name of player with ID {self.whoscored_id} for team {self.team_id} not downloaded...")
        database.insert("Players", False, self.whoscored_id, player_name,
                        f"www.whoscored.com/Players/{self.whoscored_id}/")

    def save_prev_performance_data_into_db(self):
        """update needed"""
        database.insert("Prev_Performances", False, self.prev_performance_id, self.whoscored_id, self.name,
                        self.ucl_performance_id, self.team_id, self.starting, self.bench_no_sub, self.substitute,
                        self.missing, self.duration_of_match, self.played_minutes, self.rating, self.diff_rival, self.diff_best)

    def get_data_from_db(self):
        data = database.select("Prev_Performances", Prev_Performance_ID=self.prev_performance_id)[0]
        self.starting = data['Starting']
        self.missing = data['Missing']
        self.duration_of_match = data['Duration_of_match']
        self.played_minutes = data['Played_minutes']
        self.rating = data['Rating']
        self.diff_best = data['Diff_best']
        self.diff_rival = data['Diff_rival']

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
            try:
                if self.starting == 1:
                    pitch_element = soup.find("div", attrs={'class': 'pitch-field', 'data-field': self.team.type})
                    player_elem = pitch_element.find("div", attrs={'class': 'player', 'data-player-id': self.whoscored_id})
                    rating = float(player_elem.find("span", class_='player-stat-value').string)
                elif self.substitute == 1:
                    bench_element = soup.find("div", attrs={'class': 'substitutes', 'data-field': self.team.type})
                    player_elem = bench_element.find("div", attrs={'class': 'player', 'data-player-id': self.whoscored_id})
                    rating = float(player_elem.find("span", class_='player-stat-value').string)
                else:
                    rating = 0
            except TypeError:
                logger.write(f"TypeError in get_rating(). Rating returned as 0. Prev_Performance: {self.prev_performance_id}", level=logging.ERROR)
                rating = 0 
        return rating

    def analyze_incidents(self):
        data = {'sub out': None, 'sub in': None, 'goals': 0, 'assists': 0, 'own goal': 0, 'errors': 0, 'bonuses': 0,
                'yellow card': 0, 'red card': None}
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
            try:
                assert self.substitute == 1 and data["sub in"] is not None
            except AssertionError as e:
                warnings.write(f"{self.prev_performance_id} -> AssertionError assert self.substitute == 1 and data['sub in'] is not None. Content: {e}")
                warning.write(f"data: {data}. substitute: {self.substitute}")
        return data

already_analyzed_matches = [match['UCL_Match_WhoScored_ID'] for match in database.select("Analyzed_UCL_Matches")]

# for game in database.select("UCL_Matches", order_by="Date"):
for game in (1370007, 1017562):
    '''if game['UCL_Match_WhoScored_ID'] in already_analyzed_matches:
                    logger.write(f"Match with ID {game['UCL_Match_WhoScored_ID']} was already analyzed.")
                    continue'''
    # analysis = Match.analyze_match(game['UCL_Match_WhoScored_ID'])
    analysis = Match.analyze_match(game)
    database.insert("Analyzed_UCL_Matches", True, analysis.match_id_in_database, analysis.whoscored_id)
    database.commit()
    # logger.write(f"Match with ID {game['UCL_Match_WhoScored_ID']} analyzed.")
    logger.write(f"Match with ID {game} analyzed.")
    Match.delete_all_matches()
    Match.delete_all_matches()
    PrevMatch.delete_all_prev_matches()
    Team.delete_all_teams()
    Performance.delete_all_performances()
    Prev_Performance.delete_all_prev_performances()
    logger.write(70*"-")
database.disconnect()
