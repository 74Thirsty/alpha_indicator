import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class AlphaModel:
    def __init__(self):
        self.model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')

    def train(self, x, y):
        x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        acc = accuracy_score(y_test, self.model.predict(X_test))
        print(f"Validation Accuracy: {acc:.2%}")

    def predict(self, x):
        return self.model.predict(X)
