
# common data related modules import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# algorithms import
import time
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# tools import
from sklearn.tree import DecisionTreeRegressor, plot_tree, export_graphviz
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import log_loss
from sklearn.neighbors import KNeighborsRegressor

from statistics import mean
import warnings
from sklearn.exceptions import DataConversionWarning
warnings.filterwarnings(action='ignore', category=DataConversionWarning)

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

X = data.drop(['Starting'], axis=1)
# results
y = data[["Starting"]]

# data
ws_results = []
tree_results = []
rf_results = []
knn_results = []
svm_results = []

for i in range(1,101):
    print(f'{i} --------------------------')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)
    
    whoscored_prediction = X_test['WhoScored_Prediction']
    
    X_test_with_names = X_test
    X_train = X_train.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)
    X_test = X_test.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)
    
    # --------------------------------------------------------------------------------------------------------------------
    
    """ WhoScored predictions """
    ws_loss = log_loss(y_test, whoscored_prediction)
    print(f'LogLoss for WhoScored: {round(ws_loss, 3)}')
    ws_results.append(ws_loss)
    # --------------------------------------------------------------------------------------------------------------------
    
    """DECISION TREE"""
    tree = DecisionTreeRegressor(criterion='mse', max_depth=6)
    tree.fit(X_train, y_train)
    tree_pred = tree.predict(X_test)
    tree_loss = log_loss(y_test, tree_pred)
    
    print(f'LogLoss for Decision Tree: {round(tree_loss, 3)}')
    tree_results.append(tree_loss)
    
    # --------------------------------------------------------------------------------------------------------------------
    
    """RANDOM FOREST"""
    random_forest = RandomForestRegressor(n_estimators=137, bootstrap=True)
    random_forest.fit(X_train, y_train)
    random_forest_pred = random_forest.predict(X_test)
    random_forest_loss = log_loss(y_test, random_forest_pred)
    print(f'LogLoss for Random forest: ', round(random_forest_loss, 3))
    rf_results.append(random_forest_loss)
    
# --------------------------------------------------------------------------------------------------------------------
    
    """ K Neighbors """
    knn = KNeighborsRegressor(n_neighbors=6, weights='distance', p=1)
    knn.fit(X_train, y_train)
    knn_pred = knn.predict(X_test)
    knn_loss = log_loss(y_test, knn_pred)
    print("Log Loss for KNN: ", round(knn_loss, 3))
    knn_results.append(knn_loss)
    
    # --------------------------------------------------------------------------------------------------------------------
    
    """ SVR """
    svm = SVR(kernel='rbf', C=0.01, epsilon=0.1, gamma='scale')
    svm.fit(X_train, y_train)
    svm_pred = svm.predict(X_test)
    svm_loss = log_loss(y_test, svm_pred)
    print("Log Loss for SVR: ", round(svm_loss, 3))
    svm_results.append(svm_loss)
    
    # --------------------------------------------------------------------------------------------------------------------
    

print("THE END --------------------------")

forest_count, tree_count = 0, 0
for i in range(0, len(rf_results)):
    if i == len(rf_results):
        break
    if rf_results[i] < tree_results[i]:
        forest_count += 1
    else:
        tree_count += 1
        
print("Best was Tree: ", tree_count)
print("Best was Random forest: ", forest_count)

print(f"Avg of WhoScored: {mean(ws_results)}") 
print(f"Avg of Tree: {mean(tree_results)}") 
print(f"Avg of Forest: {mean(rf_results)}") 
print(f"Avg of KNN: {mean(knn_results)}") 
print(f"Avg of SVM: {mean(svm_results)}") 

"""
# finding feature importance (3 ways)
# 1 - Feature Importance as Gini impurity (mean decrease impurity)
fi_gini = random_forest.feature_importances_
fi_gini_results = pd.DataFrame()
fi_gini_results["Features"] = X_test.columns
fi_gini_results["Importance"] = np.round(fi_gini, decimals=5)
fi_gini_results["Importance"].round(decimals=5)
    
sorted_idx = fi_gini.argsort()
    
plt.barh(np.array(X_test.columns)[sorted_idx], fi_gini[sorted_idx])
plt.xlabel("Random Forest Feature Importance - Gini impurity")

    
# 2 - Permutation Based Feature Importance
perm_importance = permutation_importance(random_forest, X_test, y_test)
sorted_idx = perm_importance.importances_mean.argsort()
plt.barh(np.array(X_test.columns)[sorted_idx], perm_importance.importances_mean[sorted_idx])
plt.xlabel("Permutation Importance")
    
# 3 - Feature Importance from SHAP values
explainer = shap.TreeExplainer(random_forest)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test, plot_type="bar")
shap.summary_plot(shap_values, X_test)
shap.plots.force(shap_values) 
"""

"""# effectiveness of experts' prediction from WhoScored.com
whoscored_test = data['Starting']
whoscored_pred = data['Predicted']
whoscored_effectiveness = round(accuracy_score(whoscored_test, whoscored_pred), 5)
data['WhoScored_Prediction'] = data['Predicted']

data = data[data["Prev_5_start"] != 99]


# 82,51 % chance for a performance of player if he is present in thw predicted squad
whoscored_effectiveness = round(accuracy_score(data['Starting'], data['Predicted'], 5))
data['WhoScored_Prediction'] = data['Predicted']
data['WhoScored_Prediction'].replace(1, whoscored_effectiveness, inplace=True)
# chance for a performance of player if he is not present in the predicted squad
inefficiency = 1-whoscored_effectiveness
for team in pd.unique(data['Team_ID']):
    team_players = [player for index, player in data[data["Team_ID"] == team].iterrows()]
    N = len(team_players)
    players_not_predicted = [player["Performance_ID"] for player in team_players if player["WhoScored_Prediction"] == 0]
    for performance in players_not_predicted:
        data.loc[data.Performance_ID == performance, "WhoScored_Prediction"] = 11*inefficiency/(N-11)"""