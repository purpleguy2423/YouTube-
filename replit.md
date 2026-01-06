# YouTube Proxy

## Overview

YouTube Proxy is a Flask-based web application that allows users to search for YouTube videos and channels, watch embedded content, and download videos. The application provides user authentication, search history tracking, and a personal video collection feature where users can save and organize their favorite videos.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** serves as the web framework with Jinja2 templating
- **Flask-Login** handles user session management and authentication
- **Flask-WTF** provides form handling with CSRF protection
- **Flask-SQLAlchemy** manages database operations with an ORM approach

### Data Layer
- **SQLAlchemy ORM** with PostgreSQL database (configured via DATABASE_URL environment variable)
- Connection pooling enabled with pool recycling (300s) and pre-ping for reliability
- Four main models:
  - `User` - Authentication with password hashing via Werkzeug
  - `Video` - YouTube video metadata storage
  - `SearchHistory` - User search tracking
  - `UserVideo` - Association table linking users to saved videos with favorites

### YouTube Integration
- **YouTubeService** - Scrapes YouTube search results using regex pattern matching on HTML content (no official API key required)
- **DownloadService** - Uses yt-dlp library for video downloading and stream extraction
- Fallback download mechanisms in `download_helper.py` for reliability
- Cookie file (`cookies.txt`) for authenticated YouTube requests

### Caching System
- Custom in-memory cache implementation with:
  - LRU eviction policy
  - Configurable TTL (default 1 hour for searches)
  - Thread-safe operations using RLock
  - Hit/miss/eviction statistics tracking

### Frontend
- Bootstrap dark theme with custom CSS overrides
- Bootstrap Icons for UI elements
- JavaScript-based video player and download modal functionality
- Responsive design with mobile support

### Authentication Flow
- Email/password-based authentication
- Password hashing using Werkzeug's security utilities
- Session persistence with "remember me" functionality
- Protected routes using Flask-Login decorators

## External Dependencies

### Python Packages
- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **Flask-Login** - User session management
- **Flask-WTF** - Form handling and CSRF
- **yt-dlp** - YouTube video downloading
- **requests** - HTTP client for YouTube scraping
- **Werkzeug** - Password hashing and WSGI utilities

### Database
- PostgreSQL (connection string via `DATABASE_URL` environment variable)

### External Services
- YouTube (scraped, not using official API)

### Environment Variables Required
- `SESSION_SECRET` - Flask secret key for sessions
- `DATABASE_URL` - PostgreSQL connection string

### CDN Resources
- Bootstrap CSS (Replit agent dark theme)
- Bootstrap Icons