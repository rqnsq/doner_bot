#!/usr/bin/env pwsh

# Navigate to project directory
Set-Location -Path 'C:\Users\arbuz\Desktop\bots\miniapp_T'

# Run docker-compose up
& docker-compose up --remove-orphans
