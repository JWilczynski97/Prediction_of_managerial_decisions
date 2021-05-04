# common data related modules import
import pandas as pd

# algorithms import
from sklearn.ensemble import RandomForestRegressor

# tools import
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error, log_loss
from sklearn.inspection import permutation_importance

# data import
players = pd.read_csv("C:/Users/Jakub Wilczyński/PycharmProjects/Prediction of managerial decisions/Data.csv", 
                           usecols=["Performance_ID", "Player_name", "Prev_1_start", "Prev_1_missing", "Prev_1_rating",
                                    "Prev_1_diff_rival", "Prev_1_diff_best", "Prev_2_start", "Prev_2_missing", "Prev_2_rating",
                                    "Prev_2_diff_rival", "Prev_2_diff_best", "Prev_3_start", "Prev_3_missing", "Prev_3_rating",
                                    "Prev_3_diff_rival", "Prev_3_diff_best", "Prev_4_start", "Prev_4_missing", "Prev_4_rating",
                                    "Prev_4_diff_rival", "Prev_4_diff_best", "Prev_5_start", "Prev_5_missing", "Prev_5_rating",
                                    "Prev_5_diff_rival", "Prev_5_diff_best", "Prev_CL_start", "Prev_CL_missing", "Prev_CL_rating",
                                    "Missing", "Predicted", "Season_minutes", "Team_news", "Starting", "Team_ID"])

# index reset
players.reset_index(drop=True, inplace=True)
players.index += 1

# effectiveness of experts' prediction from WhoScored.com
whoscored_test = players['Starting']
whoscored_pred = players['Predicted']
ws_effectiveness = round(accuracy_score(whoscored_test, whoscored_pred), 5)
players['WhoScored_Prediction'] = players['Predicted']

# 82,51 % chance for a performance of player if he is present in thw predicted squad
players['WhoScored_Prediction'].replace(1, ws_effectiveness, inplace=True)
# 17,49 % chance for a performance of player if he is not present in the predicted squad
players['WhoScored_Prediction'].replace(0, 1-ws_effectiveness, inplace=True)

# deleting rows with missing data
X = players[players["Prev_5_start"] != 99]

team_res = {}

for team in ["Team_home_847_UCL_1238298", "Team_home_36_UCL_1152950", "Team_home_67_UCL_1152953"]:
    if team in team_res:
        continue
    X_test = X[X["Team_ID"] == team]
    y_test = X_test.drop(["Starting"], axis=1)
    y_test = X_test['Starting']
    
    X_train = X[X["Team_ID"] != team]
    y_train = X_train.drop(["Starting"], axis=1)
    y_train = X_train['Starting']
    
    whoscored_prediction = X_test['WhoScored_Prediction']
    X_train_with_team = X_train
    X_train = X_train.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Starting", "Team_ID"], axis=1)
    X_test = X_test.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Starting", "Team_ID"], axis=1)
    
    
    # the finding best parameters of random forest with GridSearchCV 
    #param_grid = {'n_estimators': np.arange(1,150), 'bootstrap': [True, False]}
    #gs = GridSearchCV(RandomForestRegressor(), param_grid=param_grid, scoring='neg_mean_squared_error')
    #gs.fit(X_train, y_train)
    #print("grid: ", gs.best_params_)       # RESULTS: n_estimators = 137, bootstrap == True
    
    # Random Forest
    random_forest = RandomForestRegressor(n_estimators=137, bootstrap=True)
    random_forest.fit(X_train, y_train)
    randomforest_pred = random_forest.predict(X_test)
    
    # RandomForrest score
    rf_mse = mean_squared_error(y_test, randomforest_pred)
    rf_loss = log_loss(y_test, randomforest_pred)
    
    # WhoScored score
    whoscored_test_score = mean_squared_error(y_test, whoscored_prediction)
    ws_loss = log_loss(y_test, whoscored_prediction)
    team_res[team] = {"X test": X_test, "Y": y_test, "Y pred": randomforest_pred}
    print(f"Result of prediction for team {team}: MES: {round(rf_mse, 3)}, LogLoss: {round(rf_loss, 3)}")

