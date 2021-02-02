# Copyright (c) Jakub Wilczyński 2020
# Module with key classes in the project.
# classes: Player, Match, Team, Performance

from tools import Database


database = Database("Match_DB_copy")

class Match:
    matches = dict()

    def __init__(self, whoscored_id):
        self.whoscored_id = whoscored_id
        self.type = type_of_match(whoscored_id)
        match_data = get_match_data_from_db(self)
        self.match_id = match_data["Match_ID"]
        self.team_home = Team(match_data["Team_1_ID"])
        self.team_away = Team(match_data["Team_2_ID"])
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
    teams = dict()      # one of teams in a match

    def __init__(self, whoscored_id, kind, match_id):      # kind is a value from ("home", "away")
        self.whoscored_id = whoscored_id
        self.type = kind
        self.match_id = match_id
        self.team_id = str(whoscored_id) + "_" + str(match_id)
        team_data = database.select("Teams", Team_ID=self.whoscored_id)
        self.team_name = team_data["Team_name"]
        self.league = team_data["League"]
        self.link = team_data["Link"]

        self.predicted_eleven = get_predicted_squad()
        self.start_squad = get_start_squad()
        self.bench = get_bench()

        Team.teams[self.whoscored_id] = self

    def __del__(self):
        del Team.teams[self.team_id]

    def get_predicted_squad(self):
        pass

    def get_lineup(self):
        pass

    def get_missing_players(self):
        pass


class Performance:
    players = dict()

    def __init__(self, player_id, team_id):
        self.whoscored_id = player_id
        self.team_id = team_id      # object in form <team_id>_<ucl_match_id>
        self.ucl_match_id = team_id.split("_")[1]
        self.performance_id = str(self.whoscored_id) + "_" + str(self.ucl_match_id)
        data = database.select("Players", Player_WhoScored_ID=self.player_id)
        self.name = data["Name"]
        self.link = data["Link"]

        Performance.players[self.performance_id] = self

    def __del__(self):
        del Performance.players[self.performance_id]

    def save_performance_into_db(self):     # table Performances: Performance_ID, Player_ID, UCL_Match_ID, Missing
        """update this method"""
        database.insert("Performances", self.performance_id, self.player_id, self.match_id, self.missing) # ...

    def get_player_data_from_db(self):
        return None

    def is_missing(self):
        pass
    
    def in_predicted_squad(self):
        pass
    
    def in_lineup(self):
        pass
