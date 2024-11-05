import os
from app import app

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(os.path.join('static', 'visualizations'), exist_ok=True)
    os.makedirs(os.path.join('static', 'temp'), exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
