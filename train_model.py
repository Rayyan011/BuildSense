import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# --- Constants ---
INPUT_CSV = "hulhumale_poi_data.csv"
MODEL_OUTPUT = "model.pkl"
FEATURES = [
    'nearby_cafes', 'nearby_groceries', 'nearby_schools',
    'nearby_houses', 'nearby_parks', 'nearby_clinics',
    'foot_traffic_score', 'distance_to_main_road' # Include simulated features
]
TARGET = 'label'

# --- Main Execution ---
if __name__ == "__main__":
    # Check if input data exists
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input data file not found at '{INPUT_CSV}'.")
        print(f"Please run collect_data.py first to generate the data.")
        exit(1)

    # Load the dataset
    print(f"Loading data from {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)

    # Handle potential missing values (e.g., if Overpass query failed for some points)
    df[FEATURES] = df[FEATURES].fillna(0) # Simple imputation: fill NaNs with 0

    # Prepare features (X) and target (y)
    X = df[FEATURES]
    y = df[TARGET]

    # Encode the string labels into numerical format
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Save the label encoder classes for later use in the API
    label_classes = label_encoder.classes_
    print(f"Label classes: {label_classes}")
    # Optional: Save the encoder itself if needed elsewhere
    # joblib.dump(label_encoder, 'label_encoder.pkl')

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded # Stratify for imbalanced classes
    )
    print(f"Training data shape: {X_train.shape}, Testing data shape: {X_test.shape}")

    # Initialize and train the RandomForestClassifier
    print("Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced') # Use class_weight for imbalance
    model.fit(X_train, y_train)

    # Evaluate the model
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=label_classes)

    print(f"\nModel Accuracy: {accuracy:.4f}")
    print("Classification Report:")
    print(report)

    # Save the trained model
    print(f"Saving model to {MODEL_OUTPUT}...")
    joblib.dump({'model': model, 'label_classes': label_classes}, MODEL_OUTPUT)

    print("Model training complete.")
