<<<<<<< HEAD
# AI Mock Interview Platform - Version 1.3

## 🎯 Overview
An advanced AI-powered mock interview platform that provides realistic interview experiences with real-time proctoring, lip sync analysis, and intelligent feedback generation.

## ✨ Key Features

### 🤖 AI-Powered Interview System
- **Dynamic Question Generation**: LLM-driven contextual questions based on JD and resume
- **Adaptive Interview Flow**: Questions adapt based on candidate responses
- **Intelligent Feedback**: Comprehensive performance analysis with detailed scoring

### 👁️ Real-Time Proctoring
- **Face Detection**: Advanced OpenCV-based face monitoring
- **Violation Tracking**: Multiple faces, no face, tab switching detection
- **Smart Termination**: Automatic interview termination for violations
- **Screenshot Evidence**: Visual proof of violations

### 🎭 Lip Sync Analysis
- **Audio-Lip Movement Detection**: Analyzes synchronization between speech and lip movement
- **Background Noise Detection**: Identifies and penalizes background music/noise
- **Multiple Speaker Detection**: Detects if multiple people are speaking
- **Realistic Scoring**: Differentiates between normal voice and actual cheating

### 📋 Resume & JD Validation
- **Smart Resume Validation**: LLM-powered resume content verification
- **JD Validation**: Ensures proper job descriptions (rejects random paragraphs)
- **Intelligent Matching**: Rule-based skill matching with detailed scoring
- **Entity Extraction**: Automatic extraction of skills, projects, certifications

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly across devices
- **Real-time Monitoring**: Live camera feed and analysis visualization
- **Interactive Charts**: Performance metrics and progress tracking
- **Professional Interface**: Clean, modern design with smooth interactions

## 🏗️ Architecture

### Backend Technologies
- **Flask**: Web framework for API endpoints
- **OpenCV**: Computer vision for face detection and monitoring
- **MediaPipe**: Advanced face landmark detection (optional)
- **Groq API**: LLM integration for intelligent question generation and feedback
- **Speech Recognition**: Voice-to-text for answer processing

### Frontend Technologies
- **HTML5/CSS3**: Modern semantic markup and styling
- **JavaScript**: Real-time client-side processing
- **Chart.js**: Dynamic data visualization
- **WebRTC**: Camera access and video streaming

### Key Components
- **Interview Routes**: Core interview flow and session management
- **Proctoring System**: Real-time monitoring and violation detection
- **Lip Sync Service**: Audio-visual synchronization analysis
- **Evaluation Service**: Performance scoring and feedback generation
- **Resume/JD Service**: Document validation and matching

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Virtual environment support
- Groq API key

### Setup Instructions

1. **Clone the Repository**
```bash
git clone https://github.com/asifakousar437/Modified-AImockInterview
cd version1.3-ai-mock-interview
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment Variables**
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the Application**
```bash
cd ai-mock-interview
python app.py
```

6. **Access the Platform**
```
http://localhost:5001
```

## 📁 Complete Project Structure

```
version1.3-ai-mock-interview/
├── ai-mock-interview/                    # Main application directory
│   ├── ai_mock_interview/               # Core application code
│   │   ├── app.py                       # Main Flask application entry point
│   │   ├── config.py                    # Configuration settings and environment
│   │   ├── routes/                      # API endpoints and route handlers
│   │   │   └── interview_routes.py      # Complete interview flow management
│   │   ├── services/                    # Business logic and service layer
│   │   │   ├── interview_service.py     # LLM-powered question generation
│   │   │   ├── jd_service.py            # Resume/JD validation and matching
│   │   │   ├── lip_sync_service.py      # Audio-visual synchronization analysis
│   │   │   ├── evaluation_service.py    # Performance scoring and feedback
│   │   │   ├── llm_service.py           # Groq API integration
│   │   │   ├── resume_service.py        # Resume text extraction
│   │   │   └── speech_service.py        # Speech-to-text processing
│   │   ├── static/                      # Frontend static assets
│   │   │   ├── js/                      # JavaScript files
│   │   │   │   ├── interview.js         # Main interview interface logic
│   │   │   │   ├── monitor.js           # Real-time monitoring and proctoring
│   │   │   │   └── chart.js             # Performance visualization charts
│   │   │   ├── css/                     # Stylesheets (if any)
│   │   │   └── images/                  # Static images and assets
│   │   │       └── 42787621ed6d40f0c30f0ae423fc572c.gif  # Recording animation
│   │   ├── templates/                   # HTML templates
│   │   │   ├── interview.html           # Main interview interface (20KB)
│   │   │   └── result.html              # Results and feedback page (25KB)
│   │   ├── utils/                       # Utility functions and helpers
│   │   │   ├── camera_monitor.py         # Face detection and monitoring
│   │   │   └── file_utils.py            # File handling utilities
│   │   ├── uploads/                     # File upload directory
│   │   └── results/                     # Interview results storage
│   ├── requirements.txt                 # Python dependencies (699 bytes)
│   ├── uploads/                         # User uploaded files
│   └── venv/                           # Virtual environment (excluded)
├── .env                                # Environment variables (83 bytes)
├── .gitignore                          # Git ignore rules
├── README.md                           # This comprehensive documentation
├── CHANGELOG.md                        # Complete version history
├── PULL_REQUEST_TEMPLATE.md            # PR template for contributors
├── setup.sh                            # Automated installation script
└── uploads/                           # Additional upload storage
```

### 📊 File Sizes and Details

#### **Core Application Files**
- `app.py` (597 bytes) - Flask application entry point
- `config.py` (115 bytes) - Configuration management
- `requirements.txt` (699 bytes) - Python dependencies

#### **Route Handlers**
- `interview_routes.py` (1059 lines) - Complete interview flow with all endpoints
  - Session management
  - Resume/JD validation
  - Interview start/end
  - Real-time monitoring
  - Result generation

#### **Service Layer (Business Logic)**
- `interview_service.py` (450 lines) - Pure LLM question generation
- `jd_service.py` (367 lines) - Document validation and skill matching
- `lip_sync_service.py` (450 lines) - Audio-visual synchronization
- `evaluation_service.py` - Performance scoring and feedback
- `llm_service.py` - Groq API integration
- `resume_service.py` - Resume text extraction
- `speech_service.py` - Speech-to-text processing

#### **Frontend Assets**
- `interview.html` (20,853 bytes) - Complete interview interface
- `result.html` (25,523 bytes) - Results and feedback display
- `interview.js` (39,717 bytes) - Main interview logic and UI
- `monitor.js` (9,289 bytes) - Real-time monitoring and proctoring
- `chart.js` (2,395 bytes) - Performance visualization
- `42787621ed6d40f0c30f0ae423fc572c.gif` (13.7MB) - Recording animation

#### **Utilities**
- `camera_monitor.py` - Face detection with OpenCV
- `file_utils.py` - File upload and processing

#### **Documentation**
- `README.md` - Complete setup and usage guide
- `CHANGELOG.md` - Detailed version history
- `PULL_REQUEST_TEMPLATE.md` - Standard PR format
- `setup.sh` - Automated installation script

## 🔧 Configuration

### Environment Variables
- `GROQ_API_KEY`: Your Groq API key for LLM functionality
- `OPENAI_API_KEY`: Optional OpenAI API key
- `ANTHROPIC_API_KEY`: Optional Anthropic API key

### Settings
- **Minimum Match Score**: 25% (configurable)
- **Violation Thresholds**: 5 violations for termination
- **Lip Sync Sensitivity**: Adjustable for different environments

## 🎯 Usage Guide

### For Candidates
1. **Upload Resume**: PDF or DOCX format with skills and experience
2. **Provide Job Description**: Detailed job requirements and qualifications
3. **Start Interview**: Enable camera and microphone for proctoring
4. **Answer Questions**: Voice responses with real-time analysis
5. **Receive Feedback**: Detailed performance report and suggestions

### For Administrators
- **Monitor Sessions**: Real-time interview monitoring
- **Review Results**: Performance analytics and candidate scoring
- **Manage Settings**: Configure thresholds and validation rules

## 📊 Performance Metrics

### Interview Scoring
- **Technical Skills**: 0-5 scale based on answer accuracy
- **Communication**: Clarity, confidence, and articulation
- **Relevance**: Answer alignment with questions
- **Overall Performance**: Weighted average of all metrics

### Proctoring Analysis
- **Face Detection**: Continuous monitoring for presence
- **Lip Sync Score**: Audio-visual synchronization percentage
- **Violation Count**: Number of rule infractions
- **Termination Reason**: Cause of interview termination

## 🔍 Features in Detail

### Smart Resume Validation
- LLM-powered content analysis
- Rejects non-resume documents
- Extracts skills, projects, certifications
- Validates professional format

### JD-Resume Matching
- Rule-based skill matching algorithm
- Direct and related skill detection
- Experience and project relevance scoring
- Minimum 25% match requirement

### Real-Time Proctoring
- Face detection using OpenCV Haar cascades
- Multiple face identification
- No face detection warnings
- Tab switching monitoring
- Automatic violation tracking

### Lip Sync Analysis
- Audio level monitoring
- Lip movement detection
- Background noise identification
- Multiple speaker detection
- Realistic scoring (90-95% for normal voice)

### Question Generation
- No fallback questions - pure LLM generation
- Contextual first questions based on JD and resume
- Adaptive follow-up questions based on previous answers
- Technology-specific questioning

## 🛠️ Development

### Adding New Features
1. **Backend**: Add services in `services/` directory
2. **Frontend**: Update JavaScript in `static/js/`
3. **API**: Add routes in `routes/interview_routes.py`
4. **UI**: Modify templates in `templates/`

### Testing
- **Unit Tests**: Test individual services
- **Integration Tests**: Test complete interview flow
- **UI Tests**: Test user interface interactions

## 🐛 Troubleshooting

### Common Issues
- **Flask Import Error**: Ensure virtual environment is activated
- **API Key Errors**: Check .env file configuration
- **Camera Access**: Ensure browser permissions are granted
- **Lip Sync Issues**: Check microphone permissions

### Debug Mode
Enable debug logging by setting `DEBUG=True` in config.py

## 📝 Version History

### Version 1.3 (Current)
- ✅ Removed all fallback questions (pure LLM generation)
- ✅ Enhanced JD validation (rejects random paragraphs)
- ✅ Improved lip sync detection (realistic scoring)
- ✅ Rule-based JD-Resume matching (no more fixed 40%)
- ✅ Fixed session management and termination redirects
- ✅ Enhanced error handling and user feedback

### Previous Versions
- Version 1.2: Basic interview functionality
- Version 1.1: Initial proctoring system
- Version 1.0: Core platform development

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
- **Project Repository**: https://github.com/asifakousar437/Modified-AImockInterview

**Note**: This platform is designed for educational and practice purposes. Always ensure proper consent for video and audio recording during interviews.
=======
# Modified-AImockInterview
Ai Mock interview module
>>>>>>> 975bc2ef5f9e7b3da607785d8f1748d789d21b1f
