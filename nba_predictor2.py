import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import make_column_transformer
from sklearn.metrics import mean_absolute_error
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

X_full = pd.read_csv('test_data.csv')
y = X_full.pop('Win %')

columnTypes = X_full.dtypes
simple_imputer = SimpleImputer(strategy='constant', fill_value=65)
X_full = pd.DataFrame(simple_imputer.fit_transform(X_full), columns = X_full.columns)
X_full = X_full.astype(columnTypes)

boolean_columns = X_full.select_dtypes(include='bool').columns
X_full[boolean_columns] = X_full[boolean_columns].astype(np.int64)

X_train, X_valid, y_train, y_valid = train_test_split(X_full, y, train_size=0.8, test_size=0.2)
valid_teams = X_valid['Team'].to_numpy()
X_train.drop(['Team', 'Season'], axis=1, inplace=True)
X_valid.drop(['Team', 'Season'], axis=1, inplace=True)


from tensorflow import keras

input_shape = [X_train.shape[1]]

early_stopping = keras.callbacks.EarlyStopping(
    min_delta=0.005, # minimium amount of change to count as an improvement
    patience=50, # how many epochs to wait before stopping
    restore_best_weights=True,
)

# usually val_loss/val_mae between 0.02 and 0.04
model = keras.Sequential([
    keras.layers.Dense(512, activation='relu', input_shape=input_shape),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dense(512, activation='relu'),
    keras.layers.BatchNormalization(),
    keras.layers.Dense(1, activation='sigmoid'),
])

# lacks consistency but has potential with val_mae reaching 0.02 or better half the time
# model = keras.Sequential([
#     keras.layers.BatchNormalization(input_shape=input_shape),
#     keras.layers.Dense(512, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(512, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(512, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(1, activation='sigmoid'),
# ])

# Not very good or consistent
# model = keras.Sequential([
#     keras.layers.BatchNormalization(input_shape=input_shape),
#     keras.layers.Dense(16, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(32, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(32, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(32, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(16, activation='relu'),
#     keras.layers.Dropout(0.2),
#     keras.layers.BatchNormalization(),
#     keras.layers.Dense(1),
# ])

model.compile(
    optimizer='adam',
    loss='mae',
    metrics=['mean_squared_error', 'mae']
)

history = model.fit(
    X_train, y_train,
    validation_data=(X_valid, y_valid),
    batch_size=8,
    epochs=200,
    verbose=1,
    callbacks=[early_stopping]
)

history_df = pd.DataFrame(history.history)

best_epoch = history_df['val_loss'].idxmin()
print(("Minimum Validation Loss: {:0.4f}").format(history_df['val_loss'].min()))
print(("Best Training Loss: {:0.4f}").format(history_df['loss'][best_epoch]))
print(("Best Validation MSE Loss: {:0.4f}").format(history_df['val_mean_squared_error'][best_epoch]))
print(("Best Validation MAE Loss: {:0.4f}").format(history_df['val_mae'][best_epoch]))



preds = model.predict(X_valid)
print(valid_teams)
print(y_valid.to_numpy())
print(preds)