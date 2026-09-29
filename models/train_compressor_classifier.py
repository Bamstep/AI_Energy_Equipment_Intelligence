import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

def train_compressor_models():
    # 1. Load Dataset
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "compressor_dataset.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at: {data_path}. Run generate_compressor_data.py first.")

    df = pd.read_csv(data_path)
    print("=" * 65)
    print("COMPRESSOR MODEL TRAINING & EVALUATION PIPELINE")
    print("=" * 65)
    print(f"Loaded dataset: {df.shape[0]} samples, {df.shape[1]} columns")

    # 2. Define Features & Target
    feature_cols = [
        "mass_flow_kg_s",
        "speed_rpm",
        "suction_p_bar",
        "discharge_p_bar",
        "pressure_ratio",
        "suction_t_c",
        "discharge_t_c",
        "polytropic_efficiency",
        "polytropic_head_kj_kg",
        "surge_margin_pct",
        "vibration_rms_mm_s"
    ]
    target_col = "condition_label"

    X = df[feature_cols]
    y = df[target_col]

    # 3. Train-Test Split (80/20 Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Training set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples\n")

    # 4. Model 1: Scaled Logistic Regression Pipeline
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(random_state=42, max_iter=1000))
    ])
    lr_pipeline.fit(X_train, y_train)
    y_pred_lr = lr_pipeline.predict(X_test)
    y_prob_lr = lr_pipeline.predict_proba(X_test)[:, 1]

    print("--- MODEL 1: LOGISTIC REGRESSION PERFORMANCE ---")
    print(classification_report(y_test, y_pred_lr, target_names=["Normal (0)", "Abnormal (1)"]))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob_lr):.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_lr))
    print()

    # 5. Model 2: Random Forest Pipeline
    rf_pipeline = Pipeline([
        ("classifier", RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42))
    ])
    rf_pipeline.fit(X_train, y_train)
    y_pred_rf = rf_pipeline.predict(X_test)
    y_prob_rf = rf_pipeline.predict_proba(X_test)[:, 1]

    print("--- MODEL 2: RANDOM FOREST PERFORMANCE ---")
    print(classification_report(y_test, y_pred_rf, target_names=["Normal (0)", "Abnormal (1)"]))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob_rf):.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_rf))
    print()

    # 6. Feature Importances from Random Forest
    rf_model = rf_pipeline.named_steps["classifier"]
    importances = pd.Series(rf_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("--- RANDOM FOREST FEATURE IMPORTANCES ---")
    for feat, imp in importances.items():
        print(f"{feat:<25}: {imp:.4f}")
    print("=" * 65)

    # 7. Select & Export the Best Production Pipeline (Random Forest handles non-linear surge curves)
    artifact_path = os.path.join(os.path.dirname(__file__), "compressor_condition_model.joblib")
    
    # Bundle model and metadata for production inference
    model_package = {
        "pipeline": rf_pipeline,
        "feature_names": feature_cols,
        "model_type": "RandomForestClassifier",
        "design_standards": {
            "iso_vibration_critical_mm_s": 4.5,
            "surge_margin_alarm_pct": 12.0,
            "design_efficiency": 0.82
        }
    }
    joblib.dump(model_package, artifact_path)
    print(f"Exported Production Artifact: {artifact_path}")
    print("=" * 65)

if __name__ == "__main__":
    train_compressor_models()