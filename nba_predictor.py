import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer


# def score_dataset(X_train, X_valid, y_train, y_valid):
#     model = RandomForestRegressor(n_estimators=100, random_state=0)
#     model.fit(X_train, y_train)
#     preds = model.predict(X_valid)
#     return mean_absolute_error(y_valid, preds)

X = pd.read_csv('test_data.csv')
y = X['Win %']

X.drop(['Win %'], axis=1, inplace=True)

cols_with_missing = [col for col in X.columns if X[col].isnull().any()]

simple_imputer = SimpleImputer(strategy='constant', fill_value=65)

X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, test_size=0.2)

simple_X_train = pd.DataFrame(simple_imputer.fit_transform(X_train))
simple_X_valid = pd.DataFrame(simple_imputer.transform(X_valid))

simple_X_train.columns = X_train.columns
simple_X_valid.columns = X_valid.columns

simple_X_train.drop(['Team', 'Season'], axis=1, inplace=True)
valid_teams = simple_X_valid['Team'].to_numpy()
simple_X_valid.drop(['Team', 'Season'], axis=1, inplace=True)

# print("MAE (Imputation):")
# print(score_dataset(simple_X_train, simple_X_valid, y_train, y_valid))

model = RandomForestRegressor(n_estimators=100, random_state=0)
model.fit(simple_X_train, y_train)
preds = model.predict(simple_X_valid)
print("MAE (Imputation):")
print(mean_absolute_error(y_valid, preds))

print(valid_teams)
print(y_valid.to_numpy())
print(preds)
