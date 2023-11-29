import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
# from sklearn.impute import SimpleImputer

X_full = pd.read_csv('NBA2002-2022Spreadsheet.csv')
X_full.dropna(inplace=True)

# y = X_full[['Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%']]

y = X_full[['Win%', 'Playoffs']]

X_full.drop(['Unnamed: 0', 'Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%'], axis=1, inplace=True)

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

object_columns = X_full.select_dtypes(include='object').columns.drop(['Team', 'Season'])
X_full[object_columns] = X_full[object_columns].astype(np.int64)

X_train, X_valid, y_train, y_valid = train_test_split(X_full, y, train_size=0.8, test_size=0.2)

X_train_teams_seasons = pd.concat([X_train.pop('Team'), X_train.pop('Season')], axis=1)
X_valid_teams_seasons = pd.concat([X_valid.pop('Team'), X_valid.pop('Season')], axis=1)

# rows_with_value = X_full.index[X_full['Season'] == '2022-2023'].tolist()
# print(X_full.loc[rows_with_value, ['Team', 'Season', 'New Coach', 'New Exec', 'Prev. Playoffs', 'Prev. Champion', 'Prev. RunnerUp', 'Prev. SOS', 'Prev. SRS']])


def score_dataset(X_train, X_valid, y_train, y_valid):
    model = RandomForestRegressor(n_estimators=250, min_samples_split=5, min_samples_leaf=2, n_jobs=2, max_leaf_nodes=80)
    model.fit(X_train, y_train)
    preds = model.predict(X_valid)

    print('Actual Result:')
    print(pd.concat([X_valid_teams_seasons, y_valid], axis=1))

    print('\n\n')

    print('Predicted Result:')
    df = pd.DataFrame(preds)
    df.columns = y_valid.columns
    teams_seasons = X_valid_teams_seasons.copy()
    teams_seasons.index = df.index
    df = pd.concat([teams_seasons, df], axis=1)
    print(df)

    return mean_absolute_error(y_valid, preds)

# print(f'MAE (imputation): {score_dataset(X_train, X_valid, y_train, y_valid)}')


from tensorflow import keras
import tensorflow as tf

input_shape = [X_train.shape[1]]

bool_cols = y_train.select_dtypes(include='bool').columns

y_train[bool_cols] = y_train[bool_cols].astype(np.int64)
y_valid[bool_cols] = y_valid[bool_cols].astype(np.int64)

early_stopping = keras.callbacks.EarlyStopping(
    min_delta=0.001, # minimium amount of change to count as an improvement
    patience=100, # how many epochs to wait before stopping,
    restore_best_weights=True,
    start_from_epoch=50
)

# usually val_loss/val_mae between 0.02 and 0.04
model = keras.Sequential([
    keras.layers.Dense(512, activation='relu', input_shape=input_shape),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.BatchNormalization(),
    keras.layers.Dense(len(y.columns), activation='sigmoid'), # sigmoid?, relu?
])

def weighted_mae(y_true, y_pred):
    weights = np.array([82, 10]) # 8, 1, 0.25, 0.25; 82, 13, 2.5, 2.5; 82, 1, 1, 1
    mae = tf.abs(y_true - y_pred)
    weighted_mae = mae * weights
    mean = tf.reduce_mean(weighted_mae, axis=-1)
    return mean

def new_weighted_mae(y_true, y_pred):
    # y_true.index = y_pred.index

    weighted_wins = tf.abs(y_true[0] - y_pred[0])*82
    weighted_wins = tf.reduce_mean(weighted_wins)
    # print(weighted_wins) # ==> average wins disparity

    weighted_playoff = tf.cast(y_true[1], tf.float32) - tf.cast(tf.round(y_pred[1]), tf.float32)
    weighted_playoff = tf.abs(weighted_playoff)
    weighted_playoff = tf.reduce_sum(weighted_playoff)/126
    # print(weighted_playoff) # ==> average incorrect

    # print(weighted_wins + weighted_playoff)
    return (weighted_wins + weighted_playoff)/2

model.compile(
    optimizer= keras.optimizers.Adam(learning_rate=0.001), #'adam',
    loss= weighted_mae, #'mae',
    metrics=['mean_squared_error', 'mae']
)

history = model.fit(
    X_train, y_train,
    validation_data=(X_valid, y_valid),
    batch_size=50,
    epochs=500,
    verbose=1,
    callbacks=[early_stopping]
)

history_df = pd.DataFrame(history.history)

best_epoch = history_df['val_loss'].idxmin()
print(("Minimum Validation Loss: {:0.4f}").format(history_df['val_loss'].min()))
print(("Best Training Loss: {:0.4f}").format(history_df['loss'][best_epoch]))
print(("Best Validation MSE Loss: {:0.4f}").format(history_df['val_mean_squared_error'][best_epoch]))
print(("Best Validation MAE Loss: {:0.4f}").format(history_df['val_mae'][best_epoch]))

print('\n\n')

print('Test Result:')

preds = model.predict(X_train)
df = pd.DataFrame(preds)
df.columns = y_valid.columns
df = df.add_prefix('Predicted ')

teams_seasons = X_train_teams_seasons.copy()
teams_seasons.index = df.index

train = y_train.copy(0)
train.index = df.index
train = train.add_prefix('Actual ')

df = pd.concat([teams_seasons, df, train], axis=1)
print(df)

win_diff = tf.abs(df['Predicted Win%'] - df['Actual Win%'])
print(f'Average Win Difference: {float(tf.reduce_mean(win_diff))*82}')

playoff_wrong = int(tf.reduce_sum(tf.abs(tf.cast(tf.round(df['Predicted Playoffs']), tf.int64)-tf.round(df['Actual Playoffs']))))
print(f'Playoff Correct % : {(126-playoff_wrong)/126:3f}')

print('\n\n')


print('Validation Result:')
preds = model.predict(X_valid)

df = pd.DataFrame(preds)
df.columns = y_valid.columns

# print(new_weighted_mae(y_valid, df))
df = df.add_prefix('Predicted ')

teams_seasons = X_valid_teams_seasons.copy()
teams_seasons.index = df.index

valid = y_valid.copy(0)
valid.index = df.index
valid = valid.add_prefix('Actual ')

df = pd.concat([teams_seasons, df, valid], axis=1)
print(df)

win_diff = tf.abs(df['Predicted Win%'] - df['Actual Win%'])
print(f'Average Win Difference: {float(tf.reduce_mean(win_diff))*82}')

playoff_wrong = int(tf.reduce_sum(tf.abs(tf.cast(tf.round(df['Predicted Playoffs']), tf.int64)-tf.round(df['Actual Playoffs']))))
print(f'Playoff Correct % : {(126-playoff_wrong)/126:3f}')

print('\n\n')

