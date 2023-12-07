import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
# from sklearn.impute import SimpleImputer

X_full = pd.read_csv('NBA2002-2022Spreadsheet.csv')
X_test = pd.read_csv('NBA2022-2024Spreadsheet.csv')

X_full.dropna(inplace=True)
X_test.dropna(inplace=True)
X_test.reset_index(drop=True, inplace=True)

# y = X_full[['Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%']]

y = X_full[['Win%', 'Playoffs']]

X_full.drop(['Unnamed: 0', 'Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%'], axis=1, inplace=True)
X_test.drop(['Unnamed: 0', 'Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%'], axis=1, inplace=True)

pipeline = Pipeline([
    ('scalar', StandardScaler())
])

general_cols = list(X_full.columns)
cols_to_remove = {'Team', 'Season', 'New Coach', 'New Exec', 'Prev. Playoffs', 'Prev. Champion', 'Prev. RunnerUp'}
general_cols = list(filter(lambda x: x not in cols_to_remove, general_cols))

for curr_year in range(2003, 2024):
    curr_season = f'{curr_year-1}-{curr_year}'
    rows_with_value = X_full.index[X_full['Season'] == curr_season].tolist()
    scaled_data = pipeline.fit_transform(X_full.loc[rows_with_value, general_cols])
    X_full.loc[rows_with_value, general_cols] = scaled_data

scaled_data = pipeline.fit_transform(X_test.loc[:, general_cols])
X_test.loc[:, general_cols] = scaled_data

object_columns = X_full.select_dtypes(include='object').columns.drop(['Team', 'Season'])
X_full[object_columns] = X_full[object_columns].astype(np.int64)
object_columns = X_test.select_dtypes(include='object').columns.drop(['Team', 'Season'])
X_test[object_columns] = X_test[object_columns].astype(np.int64)

X_train, X_valid, y_train, y_valid = train_test_split(X_full, y, train_size=0.8, test_size=0.2)

X_train_teams_seasons = pd.concat([X_train.pop('Team'), X_train.pop('Season')], axis=1)
X_valid_teams_seasons = pd.concat([X_valid.pop('Team'), X_valid.pop('Season')], axis=1)
X_test_teams_season = pd.concat([X_test.pop('Team'), X_test.pop('Season')], axis=1)

# rows_with_value = X_full.index[X_full['Season'] == '2022-2023'].tolist()
# print(X_full.loc[rows_with_value, ['Team', 'Season', 'New Coach', 'New Exec', 'Prev. Playoffs', 'Prev. Champion', 'Prev. RunnerUp', 'Prev. SOS', 'Prev. SRS']])

# param_grid = {
# }

# scoring = {
#     'MAE': 'neg_mean_absolute_error',
# }

# rf = RandomForestRegressor(
#     n_estimators=100, 
#     min_samples_split=2, 
#     min_samples_leaf=4, 
#     n_jobs=2, 
#     criterion='absolute_error',
#     max_leaf_nodes=100,
#     warm_start=True,
#     max_features = 1,
#     min_weight_fraction_leaf=0.5
# )
# grid_search = GridSearchCV(
#     estimator=rf, 
#     param_grid=param_grid, 
#     cv=5, 
#     scoring='neg_mean_absolute_error', 
#     verbose=2,
#     n_jobs=2
# )

# grid_search.fit(X_train, y_train)

# best_params = grid_search.best_params_
# best_score = grid_search.best_score_

# print(f'Best Hyperparameters: {best_params}')
# print(f'Best Score: {-best_score}')

# """
def score_dataset(X_train, X_valid, y_train, y_valid):

    # model = RandomForestRegressor(
    #     n_estimators=100, 
    #     min_samples_split=2, 
    #     min_samples_leaf=4, 
    #     n_jobs=2, 
    #     criterion='absolute_error',
    #     max_leaf_nodes=100,
    #     warm_start=True,
    #     max_features = 1,
    #     min_weight_fraction_leaf=0.5
    # )
    
    model = RandomForestRegressor(
        n_estimators=100, 
        min_samples_split=2, 
        min_samples_leaf=4, 
        n_jobs=2, 
        warm_start=True,
        random_state=67
    )
    
    model.fit(X_train, y_train)
    preds = model.predict(X_valid)

    print('Validation:')
    df = pd.DataFrame(preds)
    df.columns = y_valid.columns
    df = df.add_prefix('Predicted ')
    teams_seasons = X_valid_teams_seasons.copy()
    teams_seasons.index = df.index
    valid = y_valid.copy()
    valid.index = df.index
    valid = valid.add_prefix('True ')
    df = pd.concat([teams_seasons, df, valid], axis=1)
    print(df)

    win_diff = (df['Predicted Win%'] - df['True Win%']).abs()
    print(f'Average Win Difference: {win_diff.mean()*82}')

    playoff_wrong = (df['Predicted Playoffs'].round() - df['True Playoffs']).abs().sum()
    print(f'Playoff Correct % : {(126-playoff_wrong)/126:3f}')

    return mean_absolute_error(y_valid, preds), model

result = score_dataset(X_train, X_valid, y_train, y_valid)
print(f'MAE (imputation): {result[0]}')

print('\n\n')

print('2023-2024 Season Prediction')
test_pred = pd.DataFrame(result[1].predict(X_test))
test_pred.columns = y_valid.columns
test_pred = test_pred.add_prefix('Predicted ')
test_pred = pd.concat([X_test_teams_season, test_pred], axis=1)
test_pred.sort_values(by='Predicted Win%', ascending=False, inplace=True)
test_pred.reset_index(drop=True, inplace=True)

eastern_conference = {'BOS', 'CLE', 'PHI', 'MIL', 'NYK', 'CHI', 'ATL', 'MIA', 'TOR', 'BRK', 'ORL', 'IND', 'WAS', 'DET', 'CHO'}
mask = test_pred['Team'].isin(eastern_conference)

east_standings = test_pred[mask]
west_standings = test_pred[~mask]

east_standings.reset_index(drop=True, inplace=True)
west_standings.reset_index(drop=True, inplace=True)

nba_standings = pd.concat([west_standings, east_standings], axis=1)

print(nba_standings)


# """
