# 🧹 TorrentJanitor

<div align="center">
  <img src="logo.png" alt="TorrentJanitor" width="200">
</div>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/qBittorrent-4.3%2B-brightgreen.svg" alt="qBittorrent 4.3+">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
</p>

<p align="center">
  <a href="https://github.com/sponsors/ChromuSx"><img src="https://img.shields.io/badge/Sponsor-GitHub-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white" alt="GitHub Sponsors"></a>
  <a href="https://ko-fi.com/chromus"><img src="https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://buymeacoffee.com/chromus"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
  <a href="https://www.paypal.com/paypalme/giovanniguarino1999"><img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

**Your automated cleanup service for qBittorrent**

<p align="center">
  <strong>TorrentJanitor is a Python application that automatically cleans up your qBittorrent downloads by removing problematic torrents based on customizable rules and thresholds. Like a diligent janitor, it keeps your torrent client clean, organized, and running smoothly by identifying and removing stalled, errored, or inactive torrents.</strong>
</p>

## ✨ Features

- 🧹 **Smart Cleanup**: Automatically identifies and removes problematic torrents
- ⏱️ **Grace Period System**: Configurable grace checks before removal to avoid false positives
- 🛡️ **Category Protection**: Protect important torrents by category or tracker
- 📊 **Detailed Statistics**: Track removals, freed space, and session statistics
- 🔧 **Highly Configurable**: JSON configuration with extensive customization options
- 🧪 **Dry-Run Mode**: Test your configuration without making actual changes
- 📝 **Comprehensive Logging**: Detailed logs with automatic rotation
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 🔄 **State Persistence**: Maintains state across restarts
- 🎯 **Surgical Precision**: Only removes what needs to be removed

## 📋 Requirements

- Python 3.8+
- qBittorrent 4.3+ with Web UI enabled
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Using Python

1. **Clone the repository:**
```bash
git clone https://github.com/ChromuSx/torrentjanitor.git
cd torrentjanitor
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure qBittorrent credentials:**
```bash
export QB_USERNAME="your_username"
export QB_PASSWORD="your_password"
export QB_HOST="localhost"  # or your qBittorrent host
export QB_PORT="8080"
```

4. **Run TorrentJanitor:**
```bash
# Test run (dry-run mode)
python torrentjanitor.py --once --dry-run

# Start the janitor service
python torrentjanitor.py
```

### Using Docker

1. **Build the image:**
```bash
docker build -t torrentjanitor:latest .
```

2. **Run with Docker:**
```bash
docker run -d \
  --name torrentjanitor \
  -e QB_USERNAME="your_username" \
  -e QB_PASSWORD="your_password" \
  -e QB_HOST="qbittorrent_host" \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  torrentjanitor:latest
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  torrentjanitor:
    image: torrentjanitor:latest
    container_name: torrentjanitor
    environment:
      - QB_USERNAME=${QB_USERNAME}
      - QB_PASSWORD=${QB_PASSWORD}
      - QB_HOST=qbittorrent  # or your service name
      - QB_PORT=8080
      - TZ=UTC
    volumes:
      - ./config:/config
      - ./data:/data
    restart: unless-stopped
```

## ⚙️ Configuration

TorrentJanitor uses a JSON configuration file for advanced settings. Create a `config.json` file:

```json
{
  "qbittorrent": {
    "host": "localhost",
    "port": 8080,
    "username": "admin",
    "password": "adminadmin",
    "timeout": 30
  },
  "thresholds": {
    "max_queue_time": 172800,      // 48 hours for queued torrents
    "max_meta_time": 3600,          // 1 hour for metadata download
    "min_torrent_age": 86400,       // 24 hours minimum age before removal
    "grace_checks": 3,              // Number of failed checks before removal
    "check_interval": 1800,         // 30 minutes between checks
    "min_progress_protect": 5       // Protect torrents with >5% progress
  },
  "rules": {
    "remove_errors": true,          // Remove torrents with errors
    "remove_stalled": true,          // Remove stalled torrents
    "remove_metadata_timeout": true, // Remove torrents stuck downloading metadata
    "remove_no_activity": true,      // Remove torrents with no download activity
    "remove_queue_timeout": true,    // Remove torrents queued too long
    "protect_seeding": true,         // Don't remove seeding torrents
    "protect_private_trackers": false // Protect private tracker torrents
  },
  "categories": {
    "protected": ["important", "archive"], // Never remove these categories
    "auto_remove": ["temp", "test"]        // Always remove these categories
  }
}
```

### Configuration Options

#### Thresholds
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_queue_time` | int | 172800 | Maximum seconds a torrent can be queued |
| `max_meta_time` | int | 3600 | Maximum seconds for metadata download |
| `min_torrent_age` | int | 86400 | Minimum age before considering removal |
| `grace_checks` | int | 3 | Failed checks before removal |
| `check_interval` | int | 1800 | Seconds between cleaning cycles |
| `min_progress_protect` | int | 5 | Protect torrents above this progress % |
| `min_download_speed` | int | 1024 | Minimum speed (bytes/s) to consider active |
| `min_seeds_required` | int | 1 | Minimum seeds to consider healthy |

#### Rules
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `remove_errors` | bool | true | Remove torrents with errors |
| `remove_stalled` | bool | true | Remove stalled torrents |
| `remove_metadata_timeout` | bool | true | Remove metadata timeout torrents |
| `remove_no_activity` | bool | true | Remove inactive torrents |
| `remove_queue_timeout` | bool | true | Remove long-queued torrents |
| `protect_seeding` | bool | true | Protect actively seeding torrents |
| `protect_private_trackers` | bool | false | Protect private tracker torrents |
| `min_seed_ratio` | float | 1.0 | Minimum ratio for seeding torrents |
| `max_torrent_size_gb` | int | 0 | Max size in GB (0 = unlimited) |

## 🎯 Usage Examples

### Basic Usage
```bash
# Run with default settings
python torrentjanitor.py

# Use custom config file
python torrentjanitor.py --config /path/to/config.json

# Test configuration (dry run)
python torrentjanitor.py --dry-run --once

# Verbose output for debugging
python torrentjanitor.py --verbose --once
```

### Docker Examples
```bash
# Test run with dry-run
docker run --rm \
  -e QB_USERNAME="admin" \
  -e QB_PASSWORD="adminadmin" \
  -e QB_HOST="192.168.1.100" \
  torrentjanitor:latest \
  python torrentjanitor.py --dry-run --once

# Run with custom config
docker run -d \
  --name torrentjanitor \
  -v $(pwd)/config.json:/config/config.json \
  -e QB_USERNAME="admin" \
  -e QB_PASSWORD="adminadmin" \
  torrentjanitor:latest \
  python torrentjanitor.py --config /config/config.json
```

## 🧹 What Gets Cleaned

TorrentJanitor removes torrents based on these criteria:

| Reason | Description | Configurable |
|--------|-------------|--------------|
| **ERROR_STATE** | Torrent has errors or missing files | ✅ |
| **STALLED** | Torrent is stalled (no peers/seeds) | ✅ |
| **META_TIMEOUT** | Metadata download timeout exceeded | ✅ |
| **NO_ACTIVITY** | No download activity detected | ✅ |
| **QUEUE_TIMEOUT** | Queued for too long | ✅ |
| **AUTO_CATEGORY** | Auto-remove category | ✅ |
| **LOW_RATIO** | Share ratio too low | ✅ |
| **SIZE_LIMIT** | Size limit exceeded | ✅ |

## 📝 Logging

TorrentJanitor provides comprehensive logging with automatic rotation:

- **Location**: Specified in config or `/tmp/torrentjanitor/`
- **Rotation**: Automatic when size exceeds limit
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Format**: Timestamp - Level - Message

View logs:
```bash
# Follow logs in real-time
tail -f /tmp/torrentjanitor/torrentjanitor.log

# Check Docker logs
docker logs torrentjanitor
```

## 🛡️ Protected Torrents

You can protect torrents from removal using:

1. **Categories**: Add category names to `protected` list
2. **Private Trackers**: Enable `protect_private_trackers`
3. **Seeding**: Enable `protect_seeding` for active seeds
4. **Progress**: Torrents above `min_progress_protect` %

## 📈 Statistics

TorrentJanitor tracks and reports:
- Total torrents managed
- Torrents removed per session
- Disk space freed
- Cleaning cycles performed
- Current torrent states (downloading, seeding, stalled, etc.)

Statistics are saved to `statistics.json` and logged periodically.

## 🔧 Advanced Configuration

### Using with VPN/Gluetun

If qBittorrent runs behind a VPN container:

```yaml
services:
  gluetun:
    # ... your VPN configuration
    
  qbittorrent:
    network_mode: "service:gluetun"
    # ... qBittorrent configuration
    
  torrentjanitor:
    image: torrentjanitor:latest
    environment:
      - QB_HOST=gluetun  # Use VPN container name
      - QB_PORT=8080
    depends_on:
      - gluetun
```

### Custom Scripts

You can extend TorrentJanitor by importing it:

```python
from torrentjanitor import TorrentJanitor, load_config

# Custom configuration
config = load_config()
config["thresholds"]["grace_checks"] = 5

# Create janitor with custom config
janitor = TorrentJanitor(config)

# Run custom cleaning logic
janitor.clean_torrents()
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💖 Support the Project

This project is completely free and open source. If you find it useful and would like to support its continued development and updates, consider making a donation. Your support helps keep the project alive and motivates me to add new features and improvements!

<div align="center">
  <a href="https://github.com/sponsors/ChromuSx"><img src="https://img.shields.io/badge/Sponsor-GitHub-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white" alt="GitHub Sponsors"></a>
  <a href="https://ko-fi.com/chromus"><img src="https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://buymeacoffee.com/chromus"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
  <a href="https://www.paypal.com/paypalme/giovanniguarino1999"><img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</div>

Every contribution, no matter how small, is greatly appreciated! ❤️

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [qBittorrent](https://www.qbittorrent.org/) for the excellent torrent client
- [Requests](https://requests.readthedocs.io/) for HTTP library
- All contributors and users of TorrentJanitor

## ⚠️ Disclaimer

This tool is for legitimate torrent management only. Users are responsible for complying with all applicable laws and regulations in their jurisdiction. The authors assume no liability for misuse of this software.

<p align="center">
  <b>🧹 Keep it clean, keep it lean!</b><br>
  Made with ❤️ by <a href="https://github.com/ChromuSx">Giovanni Guarino</a>
</p>
