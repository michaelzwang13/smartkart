import joblib
import numpy as np
import pandas as pd

# load model
try:
    model = joblib.load('resources/nyuhack25_600.pkl')
except Exception as e:
    print('Error loading model: ', e)
    model = None

# predict impulsive purchase
def predict_impulsive_purchase(carbs, sugar, sodium, fat):
    sample = {}
    sample['Data.Carbohydrate'] = carbs
    sample['Data.Sugar Total'] = sugar
    sample['Data.Major Minerals.Sodium'] = sodium
    sample['Data.Fat.Saturated Fat'] = fat
    sample_df = pd.DataFrame([sample])
    return model.predict(sample_df)

def model_learn(carbs, sugar, sodium, fat, label):
    x = np.array([carbs, sugar, sodium, fat])
    y = np.array([label])

    model.partial_fix(x, y)

    return model