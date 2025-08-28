#!/bin/bash

# MLS NEXT News Scraper Setup Script

echo "🚀 Setting up MLS NEXT News Scraper..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. Python $REQUIRED_VERSION+ is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create output directory
echo "📁 Creating output directory..."
mkdir -p output

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x run_scraper.sh
chmod +x test_scraper.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Test the scraper: python test_scraper.py"
echo "3. Run the scraper: python mls_next_scraper.py"
echo "4. Or use the shell script: ./run_scraper.sh"
echo ""
echo "For automated execution, set up a cron job:"
echo "crontab -e"
echo "*/30 * * * * /path/to/mls-next-news-scraper/run_scraper.sh"
echo ""
echo "Happy scraping! ⚽📰"
