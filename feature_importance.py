# common data related modules import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# algorithms import
import shap
import graphviz
# tools import
from dtreeviz.trees import dtreeviz # remember to load the package
from sklearn.tree import DecisionTreeRegressor, plot_tree, export_graphviz
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss
from sklearn.inspection import permutation_importance

# import warnings
# from sklearn.exceptions import DataConversionWarning
# warnings.filterwarnings(action='ignore', category=DataConversionWarning)

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

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)

X_test_with_names = X_test
X_train = X_train.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)
X_test = X_test.drop(["Performance_ID", "Player_name",'WhoScored_Prediction', "Team_ID"], axis=1)
 
""" DECISION TREE """
tree = DecisionTreeRegressor(criterion='mse', max_depth=6)
tree.fit(X_train, y_train)
tree_pred = tree.predict(X_test)
tree_loss = log_loss(y_test, tree_pred)

print(f'LogLoss for Decision Tree: {round(tree_loss, 3)}')

# Generating of decision tree  scheme
#fig = plt.figure(dpi=200, figsize=(200,50))
#_ = plot_tree(tree, feature_names=X_test.columns, fontsize=10, 
#              label='all', impurity=False, filled=True)
#print('Decision tree scheme generated.')
 
# finding feature importance (3 ways)
# 1 - Feature Importance as Gini impurity (mean decrease impurity)
fi_gini = tree.feature_importances_
fi_gini_results = pd.DataFrame()
fi_gini_results["Features"] = X_test.columns
fi_gini_results["Importance"] = np.round(fi_gini, decimals=5)
fi_gini_results["Importance"].round(decimals=5)
    
sorted_idx = fi_gini.argsort()
    
plt.barh(np.array(X_test.columns)[sorted_idx], fi_gini[sorted_idx])
plt.xlabel("Decision Tree Feature Importance - Gini impurity")

# 2 - Permutation Based Feature Importance
perm_importance = permutation_importance(tree, X_test, y_test)
sorted_idx = perm_importance.importances_mean.argsort()
plt.barh(np.array(X_test.columns)[sorted_idx], perm_importance.importances_mean[sorted_idx])
plt.xlabel("Permutation Importance")
    
# 3 - Feature Importance from SHAP values
explainer = shap.TreeExplainer(tree)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test, plot_type="bar")
shap.summary_plot(shap_values, X_test)
#shap.plots.force(shap_values) 
