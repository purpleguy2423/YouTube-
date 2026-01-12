#!/bin/bash
echo "Installing dependencies..."
pip install email-validator flask flask-login flask-sqlalchemy flask-wtf gunicorn oauthlib psycopg2-binary pytube pytubefix requests werkzeug wtforms youtube-dl yt-dlp
echo "Installation complete."
