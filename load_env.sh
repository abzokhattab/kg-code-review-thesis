#!/bin/bash
# Load environment variables from .env file
# Usage: source load_env.sh

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^[[:space:]]*$' | xargs)
    echo "✓ Loaded environment variables from .env"
    
    # Verify API key is set
    if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "" ]; then
        echo "✓ OpenAI API key found"
    elif [ -n "$ANTHROPIC_API_KEY" ] && [ "$ANTHROPIC_API_KEY" != "" ]; then
        echo "✓ Anthropic API key found"
    elif [ -n "$API_KEY" ] && [ "$API_KEY" != "" ]; then
        echo "✓ Generic API key found"
    else
        echo "⚠️  Warning: No API key found in .env file"
        echo "   Edit .env and add your API key"
    fi
else
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and add your credentials"
    exit 1
fi










