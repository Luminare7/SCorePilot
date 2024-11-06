# SCorePilot (SCP) - Harmony Analysis Tool

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

SCorePilot is a sophisticated music analysis tool that examines musical compositions for adherence to classical harmony rules. Built with Python and music21, it provides detailed analysis of harmony, voice leading, and compositional structure through an intuitive web interface.

## 📚 Table of Contents
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Technical Documentation](#-technical-documentation)
- [Architecture](#-architecture)
- [Development](#-development)
- [Error Reference](#-error-reference)
- [FAQ](#-faq)

## 🎵 Features

### Harmony Analysis
- **Voice Leading Analysis**
  - Parallel fifths and octaves detection
  - Voice crossing identification
  - Spacing between voices
  - Melodic interval analysis

### Chord Analysis
- **Progression Validation**
  - Root position checking
  - Weak progression detection (e.g., V-IV)
  - Cadence analysis
  - Harmonic rhythm evaluation

### Advanced Checks
- **Voice Range Verification**
  - Traditional SATB ranges
  - Excessive interval jumps
  - Hidden fifths/octaves between outer voices

### Reporting
- **Comprehensive PDF Reports**
  - Severity-based error categorization
  - Measure-specific error locations
  - Statistical analysis
  - Common issues summary

## 🚀 Installation 

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Step-by-Step Installation
```bash
# Clone the repository
git clone https://github.com/Luminare7/scorepilot.git
cd scorepilot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install MuseScore for score visualization
# Ubuntu/Debian:
sudo apt-get install musescore3
# macOS:
brew install musescore
```

### Dependencies
- **Core Libraries**
  - `music21`: Music analysis framework
  - `Flask`: Web framework
  - `ReportLab`: PDF generation
  - `Werkzeug`: File handling and security

## 💻 Usage

### Web Interface
1. Start the server:
   ```bash
   python main.py
   ```
2. Navigate to `http://localhost:5000` in your browser
3. Upload a MusicXML file
4. View analysis results and download PDF report

### Supported File Formats
- MusicXML (.musicxml, .xml)
- Compressed MusicXML (.mxl) - Coming Soon

## 📖 Technical Documentation

### Analysis Modules

#### Harmony Checker
The `HarmonyAnalyzer` class performs the following checks:
```python
analyzer = HarmonyAnalyzer()
analyzer.load_score("score.musicxml")
errors = analyzer.analyze()
```

Key Components:
- `load_score()`: Parses MusicXML and determines key
- `analyze()`: Runs all harmony checks
- `validate_score()`: Ensures score meets minimum requirements

#### Error Types
Errors are categorized by severity:
- **High**: Serious rule violations (parallel fifths/octaves)
- **Medium**: Potential issues (voice leading concerns)
- **Low**: Stylistic suggestions

## 🏗 Architecture

```
scorepilot/
├── harmony_checker/
│   ├── __init__.py
│   ├── analyzer.py        # Core analysis logic
│   ├── error_types.py     # Error definitions
│   ├── visualization.py   # Score visualization
│   ├── report_generator.py# PDF generation
│   └── utils.py          # Helper functions
├── app.py                 # Flask application
├── main.py               # Entry point
└── requirements.txt
```

## 🛠 Development

### Setting Up Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linter
flake8 .
```

### Implementing New Analysis Features

The core analysis logic is in `harmony_checker/analyzer.py`. The `HarmonyAnalyzer` class contains all music theory analysis methods.

#### Adding New Checks

1. Create a new method in the `HarmonyAnalyzer` class:
```python
def check_new_feature(self) -> None:
    """Description of what this check does"""
    if not self.score:
        return

    try:
        # Your analysis logic here
        for some_musical_element in self.score.parts:
            if some_condition:
                self.errors.append(
                    HarmonyError(
                        type='New Feature Error',
                        measure=measure_number,
                        description='Description of the error',
                        severity='medium',  # 'low', 'medium', or 'high'
                        voice1=affected_voice,  # optional
                        voice2=other_voice     # optional
                    )
                )
    except Exception as e:
        logger.error(f"Error in new feature check: {str(e)}", exc_info=True)
```

2. Add your check to the `analyze` method:
```python
def analyze(self) -> List[HarmonyError]:
    try:
        self.errors = []
        
        if not self.validate_score():
            raise Exception("Invalid score - cannot perform analysis")

        # Existing checks
        self.check_parallel_fifths()
        self.check_voice_leading()
        # ... other checks ...

        # Add your new check here
        self.check_new_feature()

        return self.errors
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise Exception(f"Analysis failed: {str(e)}")
```

#### Best Practices for New Checks

1. **Error Handling**
   - Always wrap main logic in try-except blocks
   - Log errors appropriately using the logger
   - Validate input data before processing

2. **Documentation**
   - Add detailed docstrings explaining the check
   - Document any music theory concepts being analyzed
   - Include examples of what constitutes an error

3. **Code Structure**
   - Keep methods focused and single-purpose
   - Use meaningful variable names
   - Follow existing code style and patterns

4. **Testing**
   - Add test cases for your new check
   - Include both positive and negative test cases
   - Test edge cases and error conditions

#### Common Music21 Operations

```python
# Accessing parts and notes
parts = self.score.parts
notes = parts[0].flatten().notes

# Working with intervals
interval_obj = interval.Interval(noteStart=note1, noteEnd=note2)
semitones = interval_obj.semitones
interval_name = interval_obj.simpleName  # e.g., 'P5' for perfect fifth

# Chord operations
chord = some_chord_object
is_seventh = chord.isDominantSeventh()
root = chord.root()
bass = chord.bass()
inversion = chord.inversion()

# Pitch operations
pitch = note.pitch
midi_number = pitch.midi
pitch_name = pitch.name  # e.g., 'C', 'G'
```

### Suggested Areas for New Analysis

1. **Harmony Analysis**
   - Secondary dominants detection
   - Modal mixture identification
   - Applied chord analysis
   - Advanced cadence types

2. **Voice Leading**
   - Non-chord tone analysis
   - Voice independence checks
   - Advanced part-writing rules
   - Voice range violations

3. **Form Analysis**
   - Phrase structure
   - Modulation detection
   - Thematic relationships
   - Formal boundaries

4. **Style-Specific Checks**
   - Period-specific rules
   - Genre-specific conventions
   - Composer-specific patterns

### Example Implementation

Here's an example of implementing a check for seventh chord resolutions:

```python
def check_seventh_chords(self) -> None:
    """Checks for proper resolution of seventh chords"""
    if not self.score:
        return

    try:
        chordified = self.score.chordify()
        prev_chord = None

        for chord in chordified.recurse().getElementsByClass('Chord'):
            if prev_chord and len(prev_chord.pitches) >= 4:
                try:
                    if prev_chord.isDominantSeventh():
                        resolution_note = chord.bass()
                        seventh_note = prev_chord.seventh
                        
                        # Check resolution
                        if not (seven_note.pitch.ps - resolution_note.pitch.ps == -1 or
                               seven_note.pitch.ps - resolution_note.pitch.ps == -2):
                            self.errors.append(
                                HarmonyError(
                                    type='Seventh Resolution',
                                    measure=chord.measureNumber,
                                    description='Seventh does not resolve down by step',
                                    severity='medium'
                                )
                            )
                except Exception as e:
                    logger.warning(f"Error checking seventh chord resolution: {str(e)}")
            
            prev_chord = chord

    except Exception as e:
        logger.error(f"Error in seventh chord check: {str(e)}", exc_info=True)
```

For more detailed examples and documentation, check out:
- [music21 Documentation](http://web.mit.edu/music21/doc/index.html)
- [Classical Music Theory Rules](http://openmusictheory.com/)
- [Project Wiki](https://github.com/Luminare7/scorepilot/wiki)

---

This development guide is a living document. If you implement new checks or improve existing ones, please update this documentation accordingly.

## 📋 Error Reference

### Voice Leading Errors
- **Parallel Fifths**: Consecutive perfect fifths between voices
- **Voice Crossing**: Voice moves below a lower voice
- **Large Leaps**: Melodic intervals larger than an octave

### Chord Errors
- **Non-Root Position**: Final chord not in root position
- **Weak Cadence**: Non-standard or weak cadential progression

## ❓ FAQ

### General Questions
**Q: What file formats are supported?**  
A: Currently, MusicXML (.musicxml, .xml) files are supported.

**Q: Do I need MuseScore installed?**  
A: MuseScore is optional but recommended for score visualization.

### Technical Questions
**Q: How are errors detected?**  
A: The analyzer uses music21's powerful parsing capabilities to analyze note relationships, intervals, and chord progressions.

**Q: What's the maximum file size?**  
A: The default limit is 10MB, configurable in app.py.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## 📬 Contact

- GitHub: [Luminare7](https://github.com/Luminare7)
- Project Link: [https://github.com/Luminare7/scorepilot](https://github.com/Luminare7/scorepilot)
- Issue Tracker: [Report a bug](https://github.com/Luminare7/scorepilot/issues)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Luminare7/scorepilot&type=Date)](https://star-history.com/#Luminare7/scorepilot&Date)

---

Built with ♪♫ by [Luminare7](https://github.com/Luminare7) and contributors.