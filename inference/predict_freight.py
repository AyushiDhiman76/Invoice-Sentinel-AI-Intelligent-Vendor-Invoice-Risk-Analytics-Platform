import joblib
import pandas as pd
from pathlib import Path

# Freight model path
MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "freight_cost_prediction"
    / "models"
    / "predict_freight_model.pkl"
)

def load_model():
    """
    Load trained freight prediction model
    """
    return joblib.load(MODEL_PATH)

def predict_freight_cost(input_data):
    model = load_model()

    input_df = pd.DataFrame(input_data)

    input_df["Dollars_x_Quantity"] = (
        input_df["Dollars"] * input_df["Quantity"]
    )

    X = input_df[
        ["Dollars", "Quantity", "Dollars_x_Quantity"]
    ]

    prediction = model.predict(X)

    input_df["Predicted_Freight"] = prediction.round(2)

    return input_df

if __name__ == "__main__":

    sample_data = {
    "Dollars": [1500, 9000, 3000, 200],
    "Quantity": [10, 20, 15, 5]
}

    prediction = predict_freight_cost(sample_data)

    print(prediction)