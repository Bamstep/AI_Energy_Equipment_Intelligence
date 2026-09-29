"""
AI Energy & Equipment Intelligence Suite
Module: Heat Exchanger Condition Classifier Trainer
Target: Multi-Class Operating Condition & Fouling Detection
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

FEATURE_COLUMNS = [
    "hot_mass_flow_kg_s",
    "cold_mass_flow_kg_s",
    "hot_temp_in_c",
    "hot_temp_out_c",
    "cold_temp_in_c",
    "cold_temp_out_c",
    "hot_dp_bar",
    "cold_dp_bar",
    "heat_duty_kw",
    "lmtd_c",
    "u_actual_w_m2k",
    "fouling_factor_rf_m2k_w",
    "thermal_effectiveness"
]

TARGET_COLUMN = "fault_class"

CLASS_NAMES = {
    0: "Normal Clean",
    1: "Tube-Side Fouled",
    2: "Shell-Side Fouled",
    3: "Severe Dual Fouling",
    4: "Tube Bypass / Leak"
}

def train_and_export_model(
    data_path: str = "data/heat_exchanger_telemetry.csv",
    export_dir: str = "models",
    random_state: int = 42
):
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Dataset not found at '{data_path}'. "
            "Please run 'python data/generate_heat_exchanger_data.py' first."
        )

    os.makedirs(export_dir, exist_ok=True)
    df = pd.read_csv(data_path)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y
    )

    # Standardize input features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Random Forest Benchmark
    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=4,
        random_state=random_state,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)  # Tree-based can train unscaled directly
    y_pred_rf = rf_model.predict(X_test)
    rf_acc = accuracy_score(y_test, y_pred_rf)

    # 2. HistGradientBoosting Benchmark
    hgb_model = HistGradientBoostingClassifier(
        max_iter=150,
        max_depth=8,
        random_state=random_state
    )
    hgb_model.fit(X_train_scaled, y_train)
    y_pred_hgb = hgb_model.predict(X_test_scaled)
    hgb_acc = accuracy_score(y_test, y_pred_hgb)

    print("==================================================")
    print("      HEAT EXCHANGER CLASSIFIER EVALUATION        ")
    print("==================================================")
    print(f"Random Forest Accuracy:          {rf_acc * 100:.2f}%")
    print(f"HistGradientBoosting Accuracy:   {hgb_acc * 100:.2f}%\n")

    # Select champion
    if rf_acc >= hgb_acc:
        champion_model = rf_model
        champion_name = "RandomForestClassifier"
        use_scaled = False
        final_preds = y_pred_rf
    else:
        champion_model = hgb_model
        champion_name = "HistGradientBoostingClassifier"
        use_scaled = True
        final_preds = y_pred_hgb

    print(f"Selected Champion: {champion_name}")
    print("\nClassification Report:")
    target_names = [CLASS_NAMES[i] for i in sorted(CLASS_NAMES.keys())]
    print(classification_report(y_test, final_preds, target_names=target_names))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, final_preds))

    # Calculate Gini Feature Importances (Random Forest)
    print("\nTop Thermodynamic & Hydraulic Feature Importances:")
    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    for idx in sorted_idx[:6]:
        print(f"  - {FEATURE_COLUMNS[idx]:<25}: {importances[idx]:.4f}")

    # Package and serialize artifacts
    artifact_bundle = {
        "model": champion_model,
        "scaler": scaler,
        "features": FEATURE_COLUMNS,
        "class_mapping": CLASS_NAMES,
        "use_scaled": use_scaled,
        "model_type": champion_name,
        "train_accuracy": float(max(rf_acc, hgb_acc))
    }

    model_output_path = os.path.join(export_dir, "heat_exchanger_model.joblib")
    joblib.dump(artifact_bundle, model_output_path)
    print(f"\nModel bundle serialized to: {model_output_path}")

if __name__ == "__main__":
    train_and_export_model()