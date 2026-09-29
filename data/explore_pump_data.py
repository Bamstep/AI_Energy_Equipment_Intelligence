import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_pump_eda():
    data_path = os.path.join(os.path.dirname(__file__), "pump_dataset.csv")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cannot find dataset at {data_path}. Run generate_pump_data.py first.")

    df = pd.read_csv(data_path)

    print("=" * 65)
    print("STAGE 3: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 65)
    print(f"Dataset Dimensions: {df.shape[0]} rows x {df.shape[1]} columns\n")

    print("1. DATA TYPES & MISSING VALUES:")
    info_df = pd.DataFrame({
        "Data Type": df.dtypes,
        "Missing Values": df.isnull().sum()
    })
    print(info_df)
    print("\n" + "-" * 65)

    print("2. DESCRIPTIVE STATISTICS:")
    print(df.describe().T[["mean", "std", "min", "50%", "max"]].round(2))
    print("\n" + "-" * 65)

    print("3. PEARSON CORRELATION (NUMERIC FEATURES):")
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    corr_matrix = df[numeric_cols].corr()
    print(corr_matrix.round(2))
    print("\n" + "=" * 65)

    # -----------------------------------------------------------------------
    # CLEAN DIAGNOSTIC VISUALIZATIONS (NO OVERLAPPING TEXT)
    # -----------------------------------------------------------------------
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # Plot 1: Head vs Flow Rate (Operating Map)
    sns.scatterplot(
        data=df, x="flow_rate_m3s", y="head_m", hue="condition",
        palette={"Normal": "#1f77b4", "Abnormal": "#d62728"},
        alpha=0.7, s=35, ax=axes[0, 0]
    )
    axes[0, 0].set_title("Centrifugal Pump Operating Map (Head vs Flow)", fontsize=11, fontweight="bold", pad=8)
    axes[0, 0].set_xlabel("Flow Rate Q (m³/s)")
    axes[0, 0].set_ylabel("Head H (m)")

    # Plot 2: Vibration Distribution (ISO 10816 Indicator)
    sns.kdeplot(
        data=df, x="vibration_mm_s", hue="condition",
        palette={"Normal": "#1f77b4", "Abnormal": "#d62728"},
        fill=True, common_norm=False, alpha=0.4, ax=axes[0, 1]
    )
    axes[0, 1].axvline(4.5, color="orange", linestyle="--", linewidth=1.5, label="ISO Warning (4.5 mm/s)")
    axes[0, 1].set_title("Vibration Distribution (ISO 10816 Indicator)", fontsize=11, fontweight="bold", pad=8)
    axes[0, 1].set_xlabel("Vibration Velocity RMS (mm/s)")
    axes[0, 1].set_ylabel("Density")
    axes[0, 1].legend()

    # Plot 3: Efficiency vs Flow Rate
    sns.scatterplot(
        data=df, x="flow_rate_m3s", y="efficiency", hue="condition",
        palette={"Normal": "#1f77b4", "Abnormal": "#d62728"},
        alpha=0.7, s=35, ax=axes[1, 0]
    )
    axes[1, 0].set_title("Pump Efficiency vs Flow Rate", fontsize=11, fontweight="bold", pad=8)
    axes[1, 0].set_xlabel("Flow Rate Q (m³/s)")
    axes[1, 0].set_ylabel("Efficiency (η)")

    # Plot 4: Input Power vs Flow Rate
    sns.scatterplot(
        data=df, x="flow_rate_m3s", y="input_power_kw", hue="condition",
        palette={"Normal": "#1f77b4", "Abnormal": "#d62728"},
        alpha=0.7, s=35, ax=axes[1, 1]
    )
    axes[1, 1].set_title("Shaft Input Power vs Flow Rate", fontsize=11, fontweight="bold", pad=8)
    axes[1, 1].set_xlabel("Flow Rate Q (m³/s)")
    axes[1, 1].set_ylabel("Input Power (kW)")

    # Add vertical and horizontal padding to prevent overlapping titles/axes
    plt.subplots_adjust(hspace=0.35, wspace=0.25)
    
    print("Clean diagnostic plot displayed. Close the window when done.")
    plt.show()

if __name__ == "__main__":
    run_pump_eda()