#!/bin/bash
# Script de sauvegarde automatique de db.sqlite3
# Usage: ./backup_db.sh

SRC_DB="/home/pfa/Desktop/tunijob/db.sqlite3"
BACKUP_DIR="/home/pfa/Desktop/tunijob/backups"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/db.sqlite3.$DATE.bak"

mkdir -p "$BACKUP_DIR"
cp "$SRC_DB" "$BACKUP_FILE"
echo "Sauvegarde effectuée : $BACKUP_FILE"