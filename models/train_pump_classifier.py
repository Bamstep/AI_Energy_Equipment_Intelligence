import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# ---------------------------------------------------------------------------
# 1. LOAD AND PREPARE DATA
# ---------------------------------------------------------------------------
def load_and_preprocess_data():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, "data", "pump_dataset.csv")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing dataset at {data_path}. Run generate_pump_data.py first.")

    df = pd.read_csv(data_path)

    # Engineering Feature Selection:
    # Drop pressure_difference_pa (redundant with head_m via Delta P = rho*g*H)
    # Drop hydraulic_power_kw (redundant with flow and head via Ph = rho*g*Q*H)
    features = [
        "flow_rate_m3s",
        "rpm",
        "head_m",
        "efficiency",
        "input_power_kw",
        "vibration_mm_s",
        "operating_hours"
    ]
    target = "condition"

    X = df[features]
    y = df[target]

    # Stratified Split: ensures train and test sets have the identical ~73/27 class balance
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    return X_train, X_test, y_train, y_test, features

# ---------------------------------------------------------------------------
# 2. TRAIN AND EVALUATE MODELS
# ---------------------------------------------------------------------------
def train_and_evaluate():
    X_train, X_test, y_train, y_test, feature_names = load_and_preprocess_data()

    print("=" * 65)
    print("STAGE 4 & 5: MACHINE LEARNING MODEL TRAINING & EVALUATION")
    print("=" * 65)
    print(f"Training Samples:   {len(X_train)}")
    print(f"Testing Samples:    {len(X_test)}")
    print(f"Features Selected:  {feature_names}")
    print("=" * 65)

    # -----------------------------------------------------------------------
    # MODEL 1: LOGISTIC REGRESSION (Linear Baseline)
    # Requires feature standardization because features have vastly different scales
    # (e.g. flow ~0.02 vs operating hours ~10,000)
    # -----------------------------------------------------------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)

    print("\n--- MODEL 1: LOGISTIC REGRESSION ---")
    print(f"Accuracy: {accuracy_score(y_test, lr_preds) * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, lr_preds))

    # -----------------------------------------------------------------------
    # MODEL 2: DECISION TREE CLASSIFIER (Non-Linear, Interpretable)
    # Tree models do not require scaling; we limit max_depth to prevent overfitting
    # -----------------------------------------------------------------------
    dt_model = DecisionTreeClassifier(max_depth=4, random_state=42)
    dt_model.fit(X_train, y_train)
    dt_preds = dt_model.predict(X_test)

    print("\n--- MODEL 2: DECISION TREE CLASSIFIER (max_depth=4) ---")
    print(f"Accuracy: {accuracy_score(y_test, dt_preds) * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, dt_preds))

    # Confusion Matrix for Decision Tree
    cm = confusion_matrix(y_test, dt_preds, labels=["Normal", "Abnormal"])
    print("Confusion Matrix (Decision Tree):")
    print(f"               Predicted Normal   Predicted Abnormal")
    print(f"Actual Normal        {cm[0][0]:<18} {cm[0][1]}")
    print(f"Actual Abnormal      {cm[1][0]:<18} {cm[1][1]}")
    print("\n" + "-" * 65)

    # -----------------------------------------------------------------------
    # 3. FEATURE IMPORTANCE (Engineering Explainability)
    # -----------------------------------------------------------------------
    importances = pd.Series(dt_model.feature_importances_, index=feature_names).sort_values(ascending=False)
    print("ENGINEERING FEATURE IMPORTANCE (Decision Tree):")
    for feat, imp in importances.items():
        print(f"  {feat:<22}: {imp * 100:.2f}%")
    print("-" * 65)

    # -----------------------------------------------------------------------
    # 4. SAVE ARTIFACTS
    # -----------------------------------------------------------------------
    models_dir = os.path.dirname(os.path.abspath(__file__))
    saved_model_path = os.path.join(models_dir, "pump_condition_model.joblib")
    
    # Bundle model and metadata together for inference
    artifact = {
        "model": dt_model,
        "feature_names": feature_names,
        "target_names": ["Normal", "Abnormal"]
    }
    joblib.dump(artifact, saved_model_path)
    print(f"Saved trained model artifact to: {saved_model_path}")
    print("=" * 65)

if __name__ == "__main__":
    train_and_evaluate()