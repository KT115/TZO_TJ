#!/bin/bash

# Configuration
GITHUB_USERNAME="YOUR_USERNAME"
REPO_NAME="TrayZero-TamJai"

echo "=========================================="
echo "Step 2: Initializing Git and Pushing to GitHub"
echo "=========================================="

# 1. Initialize local Git repository
git init

# 2. Stage all project files (app.py and requirements.txt)
git add .

# 3. Commit the staged files
git commit -m "Initial commit: TrayZero+ TamJai Version app and requirements"

# 4. Set branch name to main
git branch -M main

# 5. Add remote GitHub repository
git remote add origin https://github.com/KT115/TZO_TJ.git

# 6. Push code to GitHub
git push -u origin main

echo "=========================================="
echo "Push complete! Your repository is now live at:"
echo "https://github.com/KT115/TZO_TJ"
echo "=========================================="
