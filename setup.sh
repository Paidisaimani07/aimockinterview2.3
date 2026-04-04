#!/bin/bash

# AI Mock Interview Platform - Setup Script
# Version 1.3

echo "🚀 Setting up AI Mock Interview Platform v1.3..."
echo "=================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r "ai-mock-interview 4/ai-mock-interview/requirements.txt"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Optional: Add other API keys if needed
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
EOF
    echo "⚠️  Please update your .env file with your Groq API key!"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p "ai-mock-interview 4/ai-mock-interview/uploads"
mkdir -p "ai-mock-interview 4/ai-mock-interview/results"
mkdir -p "ai-mock-interview 4/ai-mock-interview/static/images"

# Create .gitkeep files for empty directories
touch "ai-mock-interview 4/ai-mock-interview/uploads/.gitkeep"
touch "ai-mock-interview 4/ai-mock-interview/results/.gitkeep"
touch "ai-mock-interview 4/ai-mock-interview/static/images/.gitkeep"

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Update your .env file with your Groq API key"
echo "2. Run the application: cd 'ai-mock-interview 4/ai-mock-interview' && python app.py"
echo "3. Open your browser to: http://localhost:5001"
echo ""
echo "📚 For detailed instructions, see README.md"
echo "🐛 For issues, check the troubleshooting section in README.md"
