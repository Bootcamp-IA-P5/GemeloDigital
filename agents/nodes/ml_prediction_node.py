import os
import sys
import pickle

# Fix Python Path
current_dir = os.path.dirname(os.path.abspath(__file__)) # agents/nodes
root_dir = os.path.dirname(os.path.dirname(current_dir)) # project root
if root_dir not in sys.path:
    sys.path.append(root_dir)

BASE_DIR = root_dir
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "path_predictor.pkl")

def predict_trajectory(competency_profile_dict: dict) -> dict:
    """
    Predicts the optimal trajectory (A -> GENERALISTA or B -> ESPECIALISTA)
    based on the user's competency profile using a pre-trained scikit-learn model.
    """
    
    print(f"\n[INFO] [Node: ML Prediction] Starting classification for Profile ID: {competency_profile_dict.get('profile_id')}...")
    
    # 1. Feature Extraction (Simplified for MVP)
    # This should match the features the model was trained on
    # E.g., [num_beginner_skills, num_advanced_skills]
    features = _extract_features(competency_profile_dict)
    
    # 2. Load Model & Predict
    prediction = "A" # Default fallback
    
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
                
            # Assume sklearn model output is ['A'] or ['B']
            # or ['GENERALISTA'] / ['ESPECIALISTA']
            raw_prediction = model.predict([features])[0]
            
            if raw_prediction in ["A", "GENERALISTA"]:
                prediction = "A"
            else:
                prediction = "B"
                
            print(f"       Model successfully loaded. Prediction: {prediction}")
        else:
            print(f"       [WARNING] Model not found at {MODEL_PATH}. Using fallback prediction: {prediction}")
            
    except Exception as e:
        print(f"       [ERROR] Failed to run prediction: {e}. Using fallback prediction: {prediction}")
        
    return {"ml_prediction": prediction}

def _extract_features(profile_dict: dict) -> list:
    """
    Extracts a numeric feature vector from the competency profile.
    """
    competencies = profile_dict.get("competencies", [])
    
    beginner_count = 0
    advanced_count = 0
    
    for comp in competencies:
        level = comp.get("level", "bajo").lower()
        if level in ["bajo", "ninguno"]:
            beginner_count += 1
        elif level in ["alto", "experto"]:
            advanced_count += 1
            
    return [beginner_count, advanced_count]

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    mock_profile = {
        "user_id": "usr_123",
        "profile_id": "prf_1",
        "competencies": [
            {"competency_id": "python", "name": "Python", "level": "alto", "score": 0.9},
            {"competency_id": "sql", "name": "SQL", "level": "alto", "score": 0.9}
        ],
        "recommended_approach": "ESPECIALISTA",
        "summary": "Mock profile"
    }
    
    final_output = predict_trajectory(mock_profile)
    print("\n[SUCCESS] FINAL OUTPUT:")
    import json
    print(json.dumps(final_output, indent=2))
