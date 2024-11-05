from app import app
from configure_music21 import configure_music21

if __name__ == "__main__":
    # Configure music21 environment first
    if not configure_music21():
        print("Warning: Could not configure music21 environment")
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
