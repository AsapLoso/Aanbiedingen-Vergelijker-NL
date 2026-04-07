import os
import sys
import kagglehub

def download_model():
    print("🚀 Starting Gemma-4 model download via kagglehub...")
    print("Note: This will download several GBs of data. Please ensure you have a stable connection.")
    
    try:
        # The specific model handle for Kaggle
        model_handle = "google/gemma-4/transformers/gemma-4-e4b-it"
        
        # Download the model
        model_path = kagglehub.model_download(model_handle)
        
        print(f"\n✅ Success! Model downloaded to:\n{model_path}")
        
        # List contents to verify
        print("\nContents of model directory:")
        for item in os.listdir(model_path):
            print(f" - {item}")
            
        return model_path
        
    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        print("\nPossible solutions:")
        print("1. Ensure you have Kaggle credentials configured (KAGGLE_USERNAME and KAGGLE_KEY).")
        print("2. Ensure you have accepted the model license on Kaggle: https://www.kaggle.com/models/google/gemma-4")
        return None

if __name__ == "__main__":
    download_model()
