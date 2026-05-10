#!/bin/bash

BASHRC_FILE="$HOME/.bashrc"
BACKUP_FILE="$HOME/.bashrc.bak.$(date +%Y%m%d_%H%M%S)"
TEMPLATE_FILE="$(dirname "$0")/bashrc_template"

echo "Updating .bashrc..."

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file not found at $TEMPLATE_FILE"
    exit 1
fi

# Create backup
cp "$BASHRC_FILE" "$BACKUP_FILE"
echo "Backup created at $BACKUP_FILE"

# Replace .bashrc
cp "$TEMPLATE_FILE" "$BASHRC_FILE"
echo ".bashrc updated successfully."
echo "Please run 'source ~/.bashrc' or restart your terminal."
