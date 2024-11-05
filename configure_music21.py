from music21 import environment
import os

def configure_music21():
    # Get music21 environment
    env = environment.Environment()
    
    # Set MuseScore path
    musescore_path = '/nix/store/jd57m9hzky1wvvbx6j4j5wj0ylp72ir0-musescore-3.6.2/bin/mscore'
    
    if os.path.exists(musescore_path):
        env['musicxmlPath'] = musescore_path
        env['musescoreDirectPNGPath'] = musescore_path
        env.write()
        return True
    return False

if __name__ == "__main__":
    configure_music21()
