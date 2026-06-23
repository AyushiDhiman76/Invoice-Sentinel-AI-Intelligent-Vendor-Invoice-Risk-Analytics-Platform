from pathlib import Path

import joblib
import pandas as pd 

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "invoice_flagging" / "models" / "predict_flag_invoice.pkl"
SCALER_PATH = BASE_DIR / "invoice_flagging" / "models" / "scaler.pkl"

def load_model(model_path:str = MODEL_PATH):
    """
    Load trained classifier model.
    """
    with open(model_path,"rb") as f:
        model = joblib.load(f)
    return model

def load_scaler(scaler_path: str = SCALER_PATH):
    with open(scaler_path, "rb") as f:
        scaler = joblib.load(f)
    return scaler

def predict_invoice_flag(input_data):
    """
    Predict invoice flag for new vendor invoices.
    """
    model = load_model()
    scaler = load_scaler()

    input_df = pd.DataFrame(input_data)

    input_scaled = scaler.transform(input_df)

    input_df["Predicted_flag"] = model.predict(input_scaled).astype(int)

    return input_df