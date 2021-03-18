# common data related modules import
import pandas as pd
import numpy as np

# visualisation modules import
import matplotlib.pyplot as plt
import seaborn as sns

# algorithms import
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

# tools import
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error, log_loss

# data import
players = pd.read_csv("./Data.csv", 
                           usecols=["Performance_ID", "Player_name", "Prev_1_start", "Prev_1_missing", "Prev_1_rating",
                                    "Prev_1_diff_rival", "Prev_1_diff_best", "Prev_2_start", "Prev_2_missing", "Prev_2_rating",
                                    "Prev_2_diff_rival", "Prev_2_diff_best", "Prev_3_start", "Prev_3_missing", "Prev_3_rating",
                                    "Prev_3_diff_rival", "Prev_3_diff_best", "Prev_4_start", "Prev_4_missing", "Prev_4_rating",
                                    "Prev_4_diff_rival", "Prev_4_diff_best", "Prev_5_start", "Prev_5_missing", "Prev_5_rating",
                                    "Prev_5_diff_rival", "Prev_5_diff_best", "Prev_CL_start", "Prev_CL_missing", "Prev_CL_rating",
                                    "Missing", "Predicted", "Season_minutes", "Team_news", "Starting"])

# index reset
players.reset_index(drop=True, inplace=True)
players.index += 1

# WhoScored effectivness
whoscored_test = players['Starting']
whoscored_pred = players['Predicted']
ws_effect = round(accuracy_score(whoscored_test, whoscored_pred), 5)

players['WhoScored_Prediction'] = players['Predicted']
players['WhoScored_Prediction'].replace(1, ws_effect, inplace=True)
players['WhoScored_Prediction'].replace(0, 1-ws_effect, inplace=True)
whoscored_all_prediction = players['WhoScored_Prediction']

# deleting rows with missing data
data = players[players["Prev_5_start"] != 99]

# data
X = data.drop(['Starting'], axis=1)
# results
y = data[["Starting",'Player_name']]
# names = ['Cristiano Ronaldo', 'Lionel Messi', 'Robert Lewandowski']

results_loss, results_mse, wh_loss, wh_mse = [], [], [], []
for i in range(1, 2):    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    whoscored_prediction = X_test['WhoScored_Prediction']
    
    y_test = y_test.query("Player_name in ['Cristiano Ronaldo', 'Lionel Messi', 'Manuel Neuer', 'Sergio Busquets', 'Robert Lewandowski']")
    X_test = X_test.query("Player_name in ['Cristiano Ronaldo', 'Lionel Messi', 'Manuel Neuer', 'Sergio Busquets', 'Robert Lewandowski']")
    y_train = y_train.drop(['Player_name'], axis=1)
    y_test = y_test.drop(['Player_name'], axis=1)

    X_train = X_train.drop(["Performance_ID", "Player_name",'WhoScored_Prediction'], axis=1)
    X_test = X_test.drop(["Performance_ID", "Player_name",'WhoScored_Prediction'], axis=1)
    

    # RandomForest algorith
    random_forest = RandomForestRegressor(n_estimators = 98)
    random_forest.fit(X_train, y_train)
    
    rf_pred = random_forest.predict(X_test)
    
    # RandomForrest score
    rf_score = mean_squared_error(y_test, rf_pred)
    rf_loss = log_loss(y_test, rf_pred)
    
    # WhoScored score
    whoscored_test_score = mean_squared_error(whoscored_prediction, y_test)
    whoscored_all_score = mean_squared_error(players['Starting'], 
                                             whoscored_all_prediction)
    ws_loss = log_loss(y_test, whoscored_prediction)
    
    """
    # Grid 
    param_grid = [{'n_estimators': np.arange(1,100)}]
    gs = GridSearchCV(random_forest, param_grid=param_grid, scoring='neg_mean_squared_error')
    gs.fit(X_train, y_train)
    print("grid: ", gs.best_params_)
    """
    
    print(f'RandomForest MSE: {round(rf_score, 3)}')
    print(f'RandomForest: {round(rf_loss, 3)}')
    print(f'WhoScored MSE: {round(whoscored_test_score, 3)}')
    print(f'WhoScored LogLoss: {round(ws_loss, 3)}')
    results_loss.append(round(rf_loss, 3))
    results_mse.append(round(rf_score, 3))
    wh_loss.append(round(ws_loss, 3))
    wh_mse.append(round(whoscored_test_score, 3))

print("-"*50)
print("Min LogLoss: ", min(results_loss))
print("Max LogLoss: ", max(results_loss))
print("Min MSE: ", min(results_mse))
print("Max MSE: ", max(results_mse))
print("-"*50)
print("Min WhoScored LogLoss: ", min(wh_loss))
print("Max WhoScored LogLoss: ", max(wh_loss))
print("Min WhoScored MSE: ", min(wh_mse))
print("Max WhoScored MSE: ", max(wh_mse))

