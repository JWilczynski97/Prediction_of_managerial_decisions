# Copyright (c) Jakub Wilczyński 2020
# The task of this program is calculation of WhoScored.com effectiveness in prediction of managerial
# decisions in the UEFA Champions League matches of the seasons from 2010/2011 to 2019/2020. This script gets data about
# predicted squads and starting line-ups from the html files with WhoScored.com webpages on the local disk.
# The program downloads necessary data and compares squads for every UEFA Champions League match having its "Preview"
# section on the WhoScored.com. Finally, program displays the result on the console.
# Tools used: Python 3.8, BeautifulSoup 4.9.1

from tools import Database, Logger
from os import listdir
from bs4 import BeautifulSoup
from sklearn.metrics import log_loss
import random

##### important structures #####
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015', '2015/2016', '2016/2017', '2017/2018',
               '2018/2019', '2019/2020']
results = {}  # dictionary included the IDs of players whose performance was correctly predicted {match : [list_of_players]}
DATABASE = 'Matches_DB.db'

########## functions ##########
def get_preview_squads(path):
    """This function gets predicted squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_preview, team_2_preview) \n
    :param path: str, path to the file with html code of Preview website"""
    with open(path, "r",
              encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        all_elements = soup.find_all("ul", class_="player")
        all_players = []
        for player in all_elements:
            all_players.append(player.get('data-playerid'))
        team_1_preview = all_players[:11]
        team_2_preview = all_players[11:]
        return team_1_preview, team_2_preview


def get_lineup_squads(path):
    """This function gets line-up squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_squad, team_2_squad)\n
    :param path: str, path to the file with html code of Match Centre website"""
    with open(path, "r",
              encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        pitch_element = soup.find_all("div", class_="pitch-field")
        team_1_squad = []
        team_1_elements = pitch_element[0].find_all("div", class_="player")
        for player in team_1_elements:
            team_1_squad.append(player.get('data-player-id'))
        team_2_squad = []
        team_2_elements = pitch_element[1].find_all("div", class_="player")
        for player in team_2_elements:
            team_2_squad.append(player.get('data-player-id'))
        return team_1_squad, team_2_squad


def compare_squads(preview, squad):
    """This function compares predicted and starting squad.
    Returns results of comparison in tuple of two lists (team_1_results, team_2_results).
    Every list includes IDs of players who were in line-up and predicted squad of the match.\n
    :param preview: tuple of two lists, predicted squads of both teams
    :param squad: tuple of two lists, line-up's of both teams"""
    team_1_result = []
    team_2_result = []
    for player in squad[0]:
        for pre_player in preview[0]:
            if pre_player == player:
                team_1_result.append(player)
                break
    for player in squad[1]:
        for pre_player in preview[1]:
            if pre_player == player:
                team_2_result.append(player)
                break
    return team_1_result, team_2_result


def check_results(result):
    """This function checks the results are correct and sensible."""
    for key, val in result.items():
        assert len(val) > 5  # 5 or less correctly predicted performances seems doubtful
        assert len(val) <= 11  # number of correctly predicted performances can't be more than 11


##### SCRIPT #####
log = Logger(log_folder=None, std_output=True)
db = Database(DATABASE, logger=log)
for season in ALL_SEASONS:
    ucl_matches = db.select("UCL_Matches", order_by='UCL_Match_ID', Season=season,)
    for match in ucl_matches:
        team_1_results, team_2_results = compare_squads(get_preview_squads(match['Preview_file']),
                                                        get_lineup_squads(match['Centre_file']))
        results[f"Match_{match['UCL_Match_ID']}_team1"] = team_1_results
        results[f"Match_{match['UCL_Match_ID']}_team2"] = team_2_results
        log.write(f"Downloading squads of match {match['UCL_Match_ID']} complete.")
    log.write(f"----- Season {season} complete.")
del db

correct_predictions = sum([int(len(res)) for res in results.values()])
all_predictions = (len(results.keys())) * 11
whoscored_effectiveness = correct_predictions / all_predictions
print(results)
log.write("Checking WhoScored effectiveness complete.\n")
log.write("RESULTS:\nAll predicted performances: " + str(all_predictions))
log.write("Correct predicted performances: " + str(correct_predictions))
log.write("WhoScored.com effectiveness: " + str(correct_predictions / all_predictions))

# RESULTS:
# All predicted performances: 24486
# Correct predicted performances: 20109
# Result: 0.8212447929429062
