#!/bin/bash
# Setup script to create .env file for Eniscope API credentials

echo "🔐 Setting up Eniscope API credentials..."
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Prompt for credentials
read -p "Enter Eniscope API URL (default: https://core.eniscope.com): " api_url
api_url=${api_url:-https://core.eniscope.com}

read -p "Enter Eniscope API Key: " api_key
read -p "Enter Eniscope Email: " email
read -sp "Enter Eniscope Password: " password
echo ""

# Create .env file
cat > .env << EOF
# Eniscope Core API Configuration
VITE_ENISCOPE_API_URL=${api_url}
VITE_ENISCOPE_API_KEY=${api_key}
VITE_ENISCOPE_EMAIL=${email}
VITE_ENISCOPE_PASSWORD=${password}

# API Timeout (milliseconds)
VITE_API_TIMEOUT=30000
EOF

echo ""
echo "✅ .env file created successfully!"
echo "📝 Note: Make sure .env is in your .gitignore file"


