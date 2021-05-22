
# common data related modules import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
# algorithms import
from sklearn.ensemble import RandomForestRegressor

# tools import
from sklearn.tree import DecisionTreeRegressor, plot_tree, export_graphviz
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import log_loss
from sklearn.neighbors import KNeighborsRegressor

# data import 
data = pd.read_csv("C:/Users/Jakub Wilczyński/PycharmProjects/Prediction of managerial decisions/Data.csv", 
                           usecols=["Performance_ID", "Player_name", "Prev_1_start", "Prev_1_missing", "Prev_1_rating",
                                    "Prev_1_diff_rival", "Prev_1_diff_best", "Prev_2_start", "Prev_2_missing", "Prev_2_rating",
                                    "Prev_2_diff_rival", "Prev_2_diff_best", "Prev_3_start", "Prev_3_missing", "Prev_3_rating",
                                    "Prev_3_diff_rival", "Prev_3_diff_best", "Prev_4_start", "Prev_4_missing", "Prev_4_rating",
                                    "Prev_4_diff_rival", "Prev_4_diff_best", "Prev_5_start", "Prev_5_missing", "Prev_5_rating",
                                    "Prev_5_diff_rival", "Prev_5_diff_best", "Prev_CL_start", "Prev_CL_missing", "Prev_CL_rating",
                                    "Missing", "Predicted", "WhoScored_Prediction", "Season_minutes", "Team_news", "Starting", "Team_ID"])


# index reset
data.reset_index(drop=True, inplace=True)
data.index += 1

# data
X = data.drop(['Starting'], axis=1)
# results
y = data[["Starting"]]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)

whoscored_prediction = X_test['WhoScored_Prediction']

X_test_with_names = X_test
X_train = X_train.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)
X_test = X_test.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)

# --------------------------------------------------------------------------------------------------------------------

"""DECISION TREE"""
param_grid_tree = {'criterion':['mse', 'friedman_mse', 'mae', 'poisson'],'max_depth': np.arange(2,20)}
gs_tree = GridSearchCV(DecisionTreeRegressor(), 
                 param_grid=param_grid_tree, 
                 scoring='neg_mean_squared_error', 
                 n_jobs = -1, verbose = 2.5)
gs_tree.fit(X_train, y_train)

print("Best parameters for Decision Tree: ", gs_tree.best_params_)   # RESULTS: criterion = 'mse, max_depht = 6

# --------------------------------------------------------------------------------------------------------------------

"""RANDOM FOREST"""
param_grid_forest = {'n_estimators': np.arange(1,150), 'bootstrap': [True, False]}
gs_forest = GridSearchCV(RandomForestRegressor(), 
                  param_grid=param_grid_forest, 
                  scoring='neg_mean_squared_error', 
                  n_jobs = -1, verbose = 2.5)
gs_forest.fit(X_train, y_train)
print("Best parameters for Random Forest: ", gs_forest.best_params_)       # RESULTS: n_estimators = 137, bootstrap == True

# --------------------------------------------------------------------------------------------------------------------

""" K NEIGHBORS """
params_knn = {'n_neighbors': range(1,21), 'weights': ['uniform','distance'], 'p': range(1,3)}
gs_knn = GridSearchCV(KNeighborsRegressor(), param_grid=params_knn, scoring="neg_mean_squared_error")
gs_knn.fit(X_train, y_train)
best_knn = gs_knn.best_params_
print("Best parameters for KNN: ", best_knn)    # RESULTS: n_neighbors = 5, p = 1, weights = 'distance'

# --------------------------------------------------------------------------------------------------------------------

""" SVR """
params_grid_svm = {'C' : [0.0001, 0.001, 0.01, 1], 'epsilon' : [0.001, 0.01, 0.1, 1],'gamma' : ('auto','scale')}
gs_svm = GridSearchCV(SVR(kernel="rbf"), 
                      param_grid=params_grid_svm,
                      scoring="neg_mean_squared_error")
gs_svm.fit(X_train, y_train)
best_svm = gs_svm.best_params_
print("Best parameters for SVR: ", best_svm)    # RESULTS: C = 0.01, epsilon = 0.1, gamma = scale


