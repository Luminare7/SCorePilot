# SCorePilot (SCP) - Your Composition Analysis Companion

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Status](https://img.shields.io/badge/status-prototype-orange)

SCorePilot (SCP) is an intelligent composition analysis tool that aims to become a comprehensive copilot for composers and musicians. Currently, it provides basic harmony and composition rule checking for MusicXML files, with plans to expand into a full-featured composition assistant.

## 🎵 Current Features

- MusicXML file analysis
- Basic harmony rule checking:
  - Parallel fifths detection
  - Voice leading analysis
  - Chord progression validation
  - Cadence verification
- PDF report generation with identified issues
- Simple web interface for file upload

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/scorepilot.git

# Install dependencies
pip install -r requirements.txt

# Run the web application
python app.py
```

Visit `http://localhost:5000` in your browser to use the application.

## 💻 Usage

1. Export your score from Sibelius/Finale/MuseScore as MusicXML
2. Upload the file through the web interface
3. Click "Analyze"
4. Download the generated PDF report

## 🛠 Technical Structure

```
scorepilot/
├── app/
│   ├── __init__.py
│   ├── analyzer/
│   │   ├── harmony_checker.py
│   │   └── score_parser.py
│   ├── pdf_generator/
│   │   └── report_builder.py
│   └── web/
│       ├── routes.py
│       └── templates/
├── tests/
├── requirements.txt
└── config.py
```

## 📋 Requirements

- Python 3.8+
- Flask
- music21
- ReportLab
- Additional requirements in `requirements.txt`

## 🗺 Roadmap

### Phase 1: Foundation (Current)
- ✅ Basic harmony analysis
- ✅ Simple web interface
- ✅ PDF report generation

### Phase 2: Enhanced Analysis (Next)
- [ ] Advanced voice leading analysis
- [ ] Style-specific rule sets
- [ ] Real-time analysis
- [ ] Interactive correction suggestions

### Phase 3: AI Integration
- [ ] Machine learning for style analysis
- [ ] Pattern recognition
- [ ] Personalized suggestions
- [ ] Performance optimization

### Phase 4: Comprehensive Copilot
- [ ] Real-time composition suggestions
- [ ] Style mimicking
- [ ] Orchestration assistance
- [ ] Collaborative features

## 🔧 Known Limitations

Current version (0.1.0) has several limitations:

1. **Analysis Scope**
   - Limited to basic harmony rules
   - No style-specific considerations
   - Basic error detection only

2. **Technical Limitations**
   - Single file processing only
   - Limited to MusicXML format
   - No real-time analysis
   - Basic PDF output

3. **Performance**
   - May be slow with large scores
   - Memory intensive for complex pieces

## 🎯 Future Improvements

1. **Analysis Capabilities**
   - Implement more advanced music theory rules
   - Add style-specific analysis
   - Include orchestration checking
   - Add counterpoint analysis

2. **User Experience**
   - Real-time feedback
   - Interactive corrections
   - Visual score markup
   - Integration with DAWs

3. **Technical Enhancements**
   - API development
   - Performance optimization
   - Support for more file formats
   - Cloud processing capabilities

4. **AI Features**
   - Style recognition
   - Composition suggestions
   - Pattern learning
   - Personalization

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas Needing Attention
1. Additional music theory rules
2. Performance optimization
3. User interface improvements
4. Testing and validation
5. Documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- music21 library team
- Flask framework
- All contributors and testers

## 📬 Contact

- Project Link: [https://github.com/yourusername/scorepilot](https://github.com/yourusername/scorepilot)
- Issue Tracker: [GitHub Issues](https://github.com/yourusername/scorepilot/issues)

---

**Note**: This is a prototype version aimed at proving the concept. Many features are planned but not yet implemented. We appreciate your patience and welcome your contributions to help make SCorePilot a comprehensive composition assistant.
