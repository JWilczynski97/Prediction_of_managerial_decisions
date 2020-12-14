# Copyright (c) Jakub Wilczyński 2020
# The task of this program is calculation of WhoScored.com effectiveness in prediction of managerial
# decisions in the UEFA Champions League matches of the seasons from 2010/2011 to 2019/2020. This script gets data about
# predicted squads and starting line-ups from the html files with WhoScored.com webpages on the local disk.
# The program downloads necessary data and compares squads for every UEFA Champions League match having its "Preview"
# section on the WhoScored.com. Finally, program displays the result on the console.
# Tools used: Python 3.8, BeautifulSoup 4.9.1

from os import listdir
from bs4 import BeautifulSoup

##### important structures #####
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015', '2015/2016', '2016/2017', '2017/2018',
               '2018/2019', '2019/2020']
results = {}  # dictionary included the IDs of players whose performance was correctly predicted {match : [list_of_players]}

########## functions ##########
def get_preview_squads(ucl_season, match_number):
    """This function gets predicted squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_preview, team_2_preview) \n
    :param match_number: int, number of match included in the name of file
    :param ucl_season: string, name of season for current match """
    with open(f"Matches\\{ucl_season.replace('/', '_')}\\Match_{str(match_number)}_preview.html", "r",
              encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        all_elements = soup.find_all("ul", class_="player")
        all_players = []
        for player in all_elements:
            all_players.append(player.get('data-playerid'))
        team_1_preview = all_players[:11]
        team_2_preview = all_players[11:]
        return team_1_preview, team_2_preview


def get_lineup_squads(ucl_season, match_number):
    """This function gets line-up squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_squad, team_2_squad)\n
    :param match_number: int, number of match included in the name of file
    :param ucl_season: string, name of season for current match"""
    with open(f"Matches\\{ucl_season.replace('/', '_')}\\Match_{str(match_number)}_squad.html", "r",
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


def matches_indexes(ucl_season):
    """This function returns indexes of matches from given season.\n
    :param ucl_season: str, name of UEFA Champions League season"""
    squads_files = list(filter(lambda x: 'squad' in x, listdir(f"Matches\\{ucl_season.replace('/','_')}")))
    ids = [int(x.split("_")[1]) for x in squads_files]
    return sorted(ids)


def check_results(result):
    """This function checks the results are correct and sensible."""
    for key, val in result.items():
        assert len(val) > 5  # number of correctly predicted performances can't be more than 11
        assert len(val) <= 11  # 5 or less correctly predicted performances seems doubtful


##### SCRIPT #####
for season in ALL_SEASONS:
    for idx in matches_indexes(season):
        team_1_results, team_2_results = compare_squads(get_preview_squads(season, idx),
                                                        get_lineup_squads(season, idx))
        results[f"Match_{str(idx)}_team1"] = team_1_results
        results[f"Match_{str(idx)}_team2"] = team_2_results
        print(f"Match {str(idx)} complete")
    print(f"----- Season {season} complete -----")

correct_predictions = 0
for match in results.keys():
    correct_predictions += int(len(results[match]))
all_predictions = (len(results.keys())) * 11
print(results)
print("RESULTS:\nAll predicted performances: " + str(all_predictions))
print("Correct predicted performances: " + str(correct_predictions))
print("WhoScored.com effectiveness: " + str(correct_predictions / all_predictions))

# RESULTS:
# All predicted performances: 24486
# Correct predicted performances: 20109
# Result: 0.8212447929429062
