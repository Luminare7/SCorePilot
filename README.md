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

### Adding New Rules
1. Define new error type in `error_types.py`
2. Add checking method in `analyzer.py`
3. Update test cases
4. Document in error reference

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