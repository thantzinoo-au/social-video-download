# 🎥 Social Video Downloader

A full-stack web application for downloading videos from various social media platforms using yt-dlp. Built with Flask (backend), React (frontend), PostgreSQL (database), and Docker for easy deployment.

## ✨ Features

- **🔐 User Authentication**: Secure login system with session management
- **🔑 API Key Management**: Generate and manage API keys for programmatic access
- **👥 Multi-user Support**: User-specific download directories and file management
- **📥 Video Downloads**: Download videos from YouTube, TikTok, Instagram, and other platforms supported by yt-dlp
- **📊 Format Selection**: Choose from available video formats and quality options
- **📁 File Management**: Browse, download, and delete your files through the web interface
- **💾 Disk Usage Monitoring**: Track storage usage and available space
- **⚡ Rate Limiting**: Built-in protection against API abuse
- **🔒 Admin Dashboard**: User management and system monitoring for administrators
- **🐳 Docker Support**: Easy deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  React Frontend │────▶│  Flask Backend   │────▶│   PostgreSQL    │
│   (Port 3000)   │     │   (Port 5001)    │     │    Database     │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  yt-dlp  │
                        │  FFmpeg  │
                        └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 2GB of free disk space
- Port 3000 and 5001 available

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/thantzinoo-au/social-video-download.git
cd social-video-download
```

2. **Create environment file**

```bash
cat > .env << EOF
# API Configuration
API_SECRET_KEY=your-super-secret-key-change-this

# Database Configuration
POSTGRES_DB=social_video_db
POSTGRES_USER=videouser
POSTGRES_PASSWORD=your-secure-password-here

# Admin User (optional - creates default admin on first run)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourSecurePassword123!

# Application Settings
DEBUG=False
MAX_FILE_SIZE=314572800  # 300MB in bytes
YTDLP_TIMEOUT=300

# User/Group IDs (optional)
UID=1000
GID=1000
EOF
```

3. **Start the application**

```bash
docker-compose up -d
```

4. **Access the application**

- Frontend: http://localhost:3000
- Backend API: http://localhost:5001
- Health Check: http://localhost:5001/health

## 📖 Usage

### Web Interface

1. **Login**: Navigate to http://localhost:3000 and login with your credentials
2. **Download Videos**:
   - Paste a video URL in the download form
   - Select desired format (optional)
   - Click "Download"
3. **Manage Files**: View, download, or delete your files from the file list
4. **API Keys**: Generate API keys for programmatic access in Settings

### API Usage

#### Authentication

```bash
# Login to get session token
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

#### Download a Video

```bash
# Using session token
curl -X POST http://localhost:5001/download \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: your-session-token" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "userId": "myuser",
    "format": "bestvideo+bestaudio/best"
  }'
```

#### List Files

```bash
curl http://localhost:5001/list-files/myuser \
  -H "X-Session-Token: your-session-token"
```

#### Get Available Formats

```bash
curl -X POST http://localhost:5001/formats \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: your-session-token" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

## 🔧 Configuration

### Environment Variables

| Variable            | Description                              | Default             |
| ------------------- | ---------------------------------------- | ------------------- |
| `API_SECRET_KEY`    | Secret key for legacy API authentication | `1234567890`        |
| `POSTGRES_DB`       | PostgreSQL database name                 | `social_video_db`   |
| `POSTGRES_USER`     | PostgreSQL username                      | `videouser`         |
| `POSTGRES_PASSWORD` | PostgreSQL password                      | `changeme123`       |
| `ADMIN_USERNAME`    | Default admin username (first run only)  | -                   |
| `ADMIN_PASSWORD`    | Default admin password (min 8 chars)     | -                   |
| `DEBUG`             | Enable debug mode                        | `False`             |
| `MAX_FILE_SIZE`     | Maximum file size in bytes               | `314572800` (300MB) |
| `YTDLP_TIMEOUT`     | Download timeout in seconds              | `300`               |
| `UID`               | User ID for file permissions             | `1000`              |
| `GID`               | Group ID for file permissions            | `1000`              |

### Backend Configuration

The backend is configured through environment variables and supports:

- Rate limiting (30 requests per minute default)
- File size validation
- URL validation
- Automatic format merging to MP4
- FFmpeg video optimization

### Frontend Configuration

The frontend connects to the backend API at `http://localhost:5001` by default. Update `src/services/api.js` to change the API endpoint.

## 📁 Project Structure

```
social-video-download/
├── backend/                 # Flask backend
│   ├── api.py              # Main API endpoints
│   ├── auth.py             # Authentication & user management
│   ├── config.py           # Configuration management
│   ├── utils.py            # Utility functions
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend Docker image
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Login.jsx
│   │   │   ├── DownloadForm.jsx
│   │   │   ├── FileList.jsx
│   │   │   ├── Settings.jsx
│   │   │   └── AdminDashboard.jsx
│   │   ├── services/       # API service layer
│   │   └── utils/          # Frontend utilities
│   ├── package.json        # Node.js dependencies
│   ├── vite.config.js      # Vite configuration
│   └── Dockerfile          # Frontend Docker image
├── downloads/              # Downloaded files (auto-created)
├── docker-compose.yml      # Docker Compose configuration
└── README.md              # This file
```

## 🔐 Security Features

- **Password Hashing**: Bcrypt with automatic salt generation
- **Session Management**: Secure session tokens with expiration
- **API Key Authentication**: Support for both session tokens and API keys
- **Rate Limiting**: Protection against brute force and abuse
- **Path Traversal Protection**: Validates file paths to prevent unauthorized access
- **Input Validation**: URL and file size validation
- **Role-Based Access Control**: Admin and user roles with different permissions

## 🛠️ Development

### Running Locally (Without Docker)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python api.py
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Building Docker Images

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

## 📊 API Endpoints

### Authentication

- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/verify` - Verify session token

### Video Operations

- `POST /download` - Download a video
- `POST /formats` - Get available formats for a URL

### File Management

- `GET /list-files/<user_id>` - List user's files
- `GET /files/<file_path>` - Download a file
- `DELETE /delete-file` - Delete a file

### User Management

- `GET /user/api-keys` - List user's API keys
- `POST /user/api-keys/create` - Create new API key
- `POST /user/api-keys/<key_id>/revoke` - Revoke API key

### Admin Endpoints

- `GET /admin/users` - List all users
- `POST /admin/users/create` - Create new user
- `GET /admin/api-keys` - List all API keys
- `POST /admin/api-keys/create` - Create API key for any user
- `POST /admin/api-keys/<key_id>/revoke` - Revoke any API key

### System

- `GET /health` - Health check endpoint
- `GET /disk-usage` - Get disk usage statistics

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful video downloader
- [Flask](https://flask.palletsprojects.com/) - The Python web framework
- [React](https://react.dev/) - The JavaScript library for building user interfaces
- [PostgreSQL](https://www.postgresql.org/) - The powerful open-source database

## 🐛 Troubleshooting

### Common Issues

**1. Container fails to start**

```bash
# Check logs
docker-compose logs backend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**2. Permission denied on downloads folder**

```bash
# Fix permissions
sudo chown -R 1000:1000 downloads/
chmod -R 755 downloads/
```

**3. Database connection error**

```bash
# Wait for database to be ready
docker-compose restart backend

# Check database health
docker-compose exec database pg_isready -U videouser
```

**4. Out of disk space**

```bash
# Check disk usage
curl http://localhost:5001/disk-usage \
  -H "X-Session-Token: your-token"

# Clean old files through the web interface or API
```

## 📞 Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Contact: [your-email@example.com]

## 🔄 Updates

To update the application:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

---

Made with ❤️ by [Your Name]
