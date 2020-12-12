# Copyright (c) Jakub Wilczyński 2020
from os import listdir
from bs4 import BeautifulSoup

##### important structures #####
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015', '2015/2016', '2016/2017', '2017/2018',
               '2018/2019', '2019/2020']
results = {}  # dictionary included the IDs of players whose performance was correctly predicted {match : [list_of_players]}
errors = []  # files with possible errors (in case unsuccessful squad downloading)

########## functions ##########
def get_preview_squads(season, match_number):
    """This function gets predicted squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_preview, team_2_preview)\n
    :param match_number: int, number of match included in the name of file
    :param season: string, name of season for current match
    """
    with open(f"Matches\\{season.replace('/', '_')}\\Match_{str(match_number)}_preview.html", "r",
              encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        all_elements = soup.find_all("ul", class_="player")
        all_players = []
        for player in all_elements:
            all_players.append(player.get('data-playerid'))
        team_1_preview = all_players[:11]
        team_2_preview = all_players[11:]
        return team_1_preview, team_2_preview


def get_lineup_squads(season, match_number):
    """This function gets line-up squad from correct file with match number.
    Returns squads of both teams in tuple of lists (team_1_squad, team_2_squad)\n
    :param match_number: int, number of match included in the name of file
    :param season: string, name of season for current match"""
    with open(f"Matches\\{season.replace('/', '_')}\\Match_{str(match_number)}_squad.html", "r",
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


def compare_squad(preview, squad):
    """This function compares predicted and starting squad.
    Returns results of comparison in tuple of two lists (team_1_results, team_2_results).
    Every list includes IDs of players who were in line-up and predicted squad of the match.\n
    :param preview: tuple of two lists, predicted squads of both teams
    :param squad: tuple of two lists, line-up's of both teams"""
    team_1_results = []
    team_2_results = []
    for player in squad[0]:
        for pre_player in preview[0]:
            if pre_player == player:
                team_1_results.append(player)
                break
    for player in squad[1]:
        for pre_player in preview[1]:
            if pre_player == player:
                team_2_results.append(player)
                break
    return team_1_results, team_2_results


def check_squads():
    """This function appends results of squads comparison to the dirctionary results."""
    matches_of_season, next_matches = 0, 0
    global errors
    for season in ALL_SEASONS:
        matches_of_season += len(list(  # number of matches in current directory/season
            filter(lambda x: "preview" in x,
                   listdir(f"Matches\\{season.replace('/', '_')}")
                   )))
        for num in range(next_matches + 1, matches_of_season + 1):
            team_1_results, team_2_results = compare_squad(get_preview_squads(season, num),
                                                           get_lineup_squads(season, num))
            if 0 in (team_1_results, team_2_results):
                errors.append(num)
            results[f"Match_{str(num)}_team1"] = team_1_results
            results[f"Match_{str(num)}_team2"] = team_2_results
            print(f"Match {str(num)} checked!")
        next_matches = matches_of_season
        print(f"----- Season {season} checked!")


def show_results():
    """This function shows results:
    1. Number of all predictions. 2. Number of correct predictions. 3. Effectiveness of WhoScored."""
    correct_predictions = 0
    for match in results.keys():
        correct_predictions += int(len(results[match]))
    all_predictions = (len(results.keys())) * 11
    print(results)
    print("RESULTS:\nAll predicted performances: " + str(all_predictions))
    print("Correct predicted performances: " + str(correct_predictions))
    print("Result: " + str(correct_predictions / all_predictions))
    if len(errors) > 0:
        print(50 * "#" + f"ERRORS in the files: {errors}")

##### SCRIPT #####
check_squads()
show_results()
