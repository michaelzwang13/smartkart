import math
import joblib
import pandas as pd

try:
    model = joblib.load('resources/nyuhack25_600.pkl')
except Exception as e:
    print('Error loading model: ', e)
    model = None