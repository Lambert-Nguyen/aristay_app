#!/bin/bash

# Deploy to Heroku from deployment-clean branch
# Usage: ./deploy.sh

echo "🚀 Deploying to Heroku..."

# Switch to deployment-clean branch
git checkout deployment-clean

# Push to Heroku main branch
git push heroku deployment-clean:main

echo "✅ Deployment complete!"
echo "🌐 App URL: https://aristay-internal-backend-72ffd16c9352.herokuapp.com/"
