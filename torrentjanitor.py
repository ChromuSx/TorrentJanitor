#!/usr/bin/env python3
"""
TorrentJanitor - Automated qBittorrent Cleanup and Maintenance
Author: Giovanni Guarino
License: MIT
Version: 1.0.0

    🧹 TorrentJanitor - Keep it clean, keep it lean! 🧹
    
    Automated cleanup service for qBittorrent
    Removes stalled, errored, and problematic torrents
    Keeps your torrent client running smoothly
"""

import json
import time
import logging
import requests
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os
import sys

__version__ = "1.0.0"
__author__ = "Giovanni Guarino"

class RemovalReason(Enum):
    """Reasons for torrent removal"""
    ERROR_STATE = "Error state or missing files"
    STALLED = "Stalled torrent"
    META_TIMEOUT = "Metadata download timeout"
    NO_ACTIVITY = "No download activity"
    QUEUE_TIMEOUT = "Queue timeout exceeded"
    AUTO_CATEGORY = "Auto-remove category"
    MANUAL = "Manual removal"
    LOW_RATIO = "Low share ratio"
    SIZE_LIMIT = "Size limit exceeded"

@dataclass
class TorrentState:
    """Monitored state of a torrent"""
    hash: str
    name: str
    count: int
    reason: str
    first_seen: float
    last_check: float
    size: Optional[int] = None
    progress: Optional[float] = None

class QBittorrentClient:
    """qBittorrent API client"""
    
    def __init__(self, host: str, port: int, username: str, password: str, 
                 timeout: int = 30, verify_ssl: bool = True):
        self.base_url = f"http://{host}:{port}/api/v2"
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.authenticated = False
        
    def login(self) -> bool:
        """Authenticate with qBittorrent"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data={"username": self.username, "password": self.password},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("✓ Successfully authenticated with qBittorrent")
                return True
            else:
                logging.error(f"Authentication failed: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Connection error: {e}")
            return False
    
    def get_torrents(self, filter: Optional[str] = None, 
                    category: Optional[str] = None) -> Optional[List[Dict]]:
        """Get list of torrents with optional filtering"""
        if not self.authenticated:
            if not self.login():
                return None
        
        try:
            params = {}
            if filter:
                params['filter'] = filter
            if category:
                params['category'] = category
                
            response = self.session.get(
                f"{self.base_url}/torrents/info",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Failed to get torrents: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logging.error(f"API error: {e}")
            self.authenticated = False
            return None
    
    def get_torrent_properties(self, hash: str) -> Optional[Dict]:
        """Get detailed properties of a specific torrent"""
        try:
            response = self.session.get(
                f"{self.base_url}/torrents/properties",
                params={"hash": hash},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def reannounce(self, hashes: List[str]) -> bool:
        """Reannounce torrents to trackers"""
        try:
            response = self.session.post(
                f"{self.base_url}/torrents/reannounce",
                data={"hashes": "|".join(hashes)},
                timeout=self.timeout
            )
            return response.status_code in [200, 204]
        except:
            return False
    
    def delete_torrents(self, hashes: List[str], delete_files: bool = True, 
                       dry_run: bool = False) -> bool:
        """Delete torrents"""
        if dry_run:
            logging.info(f"[DRY-RUN] Would delete {len(hashes)} torrent(s)")
            return True
            
        try:
            response = self.session.post(
                f"{self.base_url}/torrents/delete",
                data={
                    "hashes": "|".join(hashes),
                    "deleteFiles": str(delete_files).lower()
                },
                timeout=self.timeout
            )
            return response.status_code in [200, 204]
        except requests.RequestException as e:
            logging.error(f"Delete error: {e}")
            return False
    
    def pause_torrents(self, hashes: List[str]) -> bool:
        """Pause torrents"""
        try:
            response = self.session.post(
                f"{self.base_url}/torrents/pause",
                data={"hashes": "|".join(hashes)},
                timeout=self.timeout
            )
            return response.status_code in [200, 204]
        except:
            return False

class TorrentJanitor:
    """Main TorrentJanitor manager - Keeps your torrents clean!"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = QBittorrentClient(
            **config["qbittorrent"]
        )
        
        # Setup directories and files
        self.work_dir = Path(config["paths"]["work_dir"])
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.work_dir / config["paths"]["state_file"]
        self.log_file = self.work_dir / config["paths"]["log_file"]
        self.stats_file = self.work_dir / config["paths"].get("stats_file", "stats.json")
        
        # Setup logging
        self._setup_logging()
        
        # Load state
        self.torrent_states: Dict[str, TorrentState] = self._load_state()
        
        # Statistics
        self.stats = {
            "session_started": time.time(),
            "torrents_removed": 0,
            "space_freed": 0,
            "checks_performed": 0
        }
        
    def _setup_logging(self):
        """Configure logging system"""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_format = log_config.get("format", 
                                    '%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler with rotation
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler, console_handler]
        )
        
        # Log startup
        logging.info(f"TorrentJanitor v{__version__} starting...")
        logging.info("🧹 Ready to clean up your torrents!")
    
    def _load_state(self) -> Dict[str, TorrentState]:
        """Load persistent state"""
        if not self.state_file.exists():
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                return {
                    k: TorrentState(**v) for k, v in data.items()
                }
        except Exception as e:
            logging.warning(f"Could not load state: {e}")
            return {}
    
    def _save_state(self):
        """Save persistent state"""
        try:
            data = {
                k: asdict(v) for k, v in self.torrent_states.items()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save state: {e}")
    
    def _save_stats(self):
        """Save statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except:
            pass
    
    def _should_remove_torrent(self, torrent: Dict) -> Tuple[bool, Optional[RemovalReason]]:
        """Determine if a torrent should be removed"""
        current_time = time.time()
        thresholds = self.config["thresholds"]
        rules = self.config.get("rules", {})
        categories = self.config.get("categories", {})
        
        hash_val = torrent["hash"]
        name = torrent["name"][:100]
        state = torrent["state"]
        added_on = torrent["added_on"]
        num_seeds = torrent.get("num_seeds", 0)
        dlspeed = torrent.get("dlspeed", 0)
        progress = torrent.get("progress", 0)
        category = torrent.get("category", "")
        tracker = torrent.get("tracker", "")
        ratio = torrent.get("ratio", 0)
        size = torrent.get("size", 0)
        
        age = current_time - added_on
        
        # Protected categories
        if category in categories.get("protected", []):
            if hash_val in self.torrent_states:
                del self.torrent_states[hash_val]
            return False, None
        
        # Auto-remove categories
        if category in categories.get("auto_remove", []):
            logging.debug(f"Auto-remove category: {name}")
            return True, RemovalReason.AUTO_CATEGORY
        
        # Protect seeding torrents if configured
        if rules.get("protect_seeding", True) and state == "uploading":
            if ratio >= rules.get("min_seed_ratio", 1.0):
                return False, None
        
        # Protect private trackers if configured
        if rules.get("protect_private_trackers", False):
            if "private" in tracker.lower() or tracker in categories.get("private_trackers", []):
                return False, None
        
        # Size limits
        max_size = rules.get("max_torrent_size_gb", 0) * 1024 * 1024 * 1024
        if max_size > 0 and size > max_size and progress < 0.1:
            return True, RemovalReason.SIZE_LIMIT
        
        # 1. Immediate error states
        if rules.get("remove_errors", True) and state in ["error", "missingFiles"]:
            logging.debug(f"Error state detected: {name}")
            return True, RemovalReason.ERROR_STATE
        
        # 2. Stalled torrents
        if rules.get("remove_stalled", True) and state in ["stalledDL", "stalledUP"]:
            return self._check_with_grace(
                hash_val, name, RemovalReason.STALLED, current_time, torrent
            )
        
        # 3. Metadata timeout
        if (rules.get("remove_metadata_timeout", True) and 
            state == "metaDL" and age > thresholds["max_meta_time"]):
            return self._check_with_grace(
                hash_val, name, RemovalReason.META_TIMEOUT, current_time, torrent
            )
        
        # 4. No activity downloads
        if (rules.get("remove_no_activity", True) and
            state == "downloading" and 
            dlspeed < thresholds.get("min_download_speed", 1024) and 
            num_seeds < thresholds.get("min_seeds_required", 1) and
            progress * 100 <= thresholds["min_progress_protect"] and
            age > thresholds["min_torrent_age"]):
            return self._check_with_grace(
                hash_val, name, RemovalReason.NO_ACTIVITY, current_time, torrent
            )
        
        # 5. Queue timeout
        if (rules.get("remove_queue_timeout", True) and
            state == "queuedDL" and age > thresholds["max_queue_time"]):
            return self._check_with_grace(
                hash_val, name, RemovalReason.QUEUE_TIMEOUT, current_time, torrent
            )
        
        # 6. Low ratio (completed torrents)
        if (rules.get("remove_low_ratio", False) and
            state == "uploading" and
            ratio < rules.get("min_seed_ratio", 1.0) and
            age > thresholds.get("max_seed_time", 604800)):
            return self._check_with_grace(
                hash_val, name, RemovalReason.LOW_RATIO, current_time, torrent
            )
        
        # Remove from monitoring if now OK
        if hash_val in self.torrent_states:
            del self.torrent_states[hash_val]
        
        return False, None
    
    def _check_with_grace(self, hash_val: str, name: str, reason: RemovalReason, 
                          current_time: float, torrent: Dict) -> Tuple[bool, Optional[RemovalReason]]:
        """Check with grace period before removal"""
        grace_checks = self.config["thresholds"]["grace_checks"]
        
        if hash_val in self.torrent_states:
            state = self.torrent_states[hash_val]
            state.count += 1
            state.last_check = current_time
            state.size = torrent.get("size", 0)
            state.progress = torrent.get("progress", 0)
            
            if state.count >= grace_checks:
                logging.info(f"🗑️  Removing after {state.count} checks ({reason.value}): {name}")
                return True, reason
            else:
                logging.warning(f"⚠️  Check {state.count}/{grace_checks} for {reason.value}: {name}")
                return False, None
        else:
            # First time seeing this issue
            self.torrent_states[hash_val] = TorrentState(
                hash=hash_val,
                name=name,
                count=1,
                reason=reason.value,
                first_seen=current_time,
                last_check=current_time,
                size=torrent.get("size", 0),
                progress=torrent.get("progress", 0)
            )
            logging.warning(f"⚠️  Check 1/{grace_checks} for {reason.value}: {name}")
            return False, None
    
    def clean_torrents(self):
        """Execute cleaning cycle"""
        logging.info("=" * 60)
        logging.info("Starting torrent check cycle")
        
        self.stats["checks_performed"] += 1
        
        torrents = self.client.get_torrents()
        if not torrents:
            logging.warning("No torrents found or API error")
            return
        
        # Analyze torrents
        to_remove = []
        stats = {
            "total": len(torrents),
            "downloading": 0,
            "seeding": 0,
            "queued": 0,
            "stalled": 0,
            "metadl": 0,
            "error": 0,
            "paused": 0
        }
        
        for torrent in torrents:
            # Update statistics
            state = torrent["state"]
            if state == "downloading":
                stats["downloading"] += 1
            elif state in ["uploading", "stalledUP"]:
                stats["seeding"] += 1
            elif state == "queuedDL":
                stats["queued"] += 1
            elif state.startswith("stalled"):
                stats["stalled"] += 1
            elif state == "metaDL":
                stats["metadl"] += 1
            elif state in ["error", "missingFiles"]:
                stats["error"] += 1
            elif state in ["pausedDL", "pausedUP"]:
                stats["paused"] += 1
            
            # Check for removal
            should_remove, reason = self._should_remove_torrent(torrent)
            if should_remove:
                to_remove.append({
                    "hash": torrent["hash"],
                    "name": torrent["name"][:100],
                    "size": torrent.get("size", 0),
                    "reason": reason
                })
        
        # Remove problematic torrents
        if to_remove:
            self._process_removals(to_remove)
        else:
            logging.info("✅ No torrents to remove")
        
        # Save state
        self._save_state()
        self._save_stats()
        
        # Report statistics
        self._report_statistics(stats)
        
        # Clean old states
        self._clean_old_states(torrents)
    
    def _process_removals(self, to_remove: List[Dict]):
        """Process torrent removals"""
        logging.info(f"📊 Processing {len(to_remove)} torrent(s) for removal...")
        
        total_size = sum(t["size"] for t in to_remove)
        
        for item in to_remove:
            size_mb = item['size'] / (1024 * 1024)
            logging.info(f"   - {item['name']} ({size_mb:.1f} MB) - {item['reason'].value}")
        
        hashes = [t["hash"] for t in to_remove]
        dry_run = self.config.get("dry_run", False)
        
        if not dry_run:
            # Try reannounce first
            self.client.reannounce(hashes)
            time.sleep(2)
        
        # Delete torrents
        if self.client.delete_torrents(hashes, dry_run=dry_run):
            if dry_run:
                logging.info(f"[DRY-RUN] Would remove {len(to_remove)} torrent(s), "
                           f"freeing {total_size / (1024**3):.2f} GB")
            else:
                logging.info(f"✅ Successfully removed {len(to_remove)} torrent(s), "
                           f"freed {total_size / (1024**3):.2f} GB")
                
                # Update statistics
                self.stats["torrents_removed"] += len(to_remove)
                self.stats["space_freed"] += total_size
                
                # Clean state for removed torrents
                for hash_val in hashes:
                    if hash_val in self.torrent_states:
                        del self.torrent_states[hash_val]
        else:
            logging.error("❌ Failed to remove torrents")
    
    def _report_statistics(self, stats: Dict):
        """Report current statistics"""
        logging.info("📈 Current Statistics:")
        logging.info(f"   Total: {stats['total']} | Downloading: {stats['downloading']} | "
                    f"Seeding: {stats['seeding']}")
        logging.info(f"   Queued: {stats['queued']} | Stalled: {stats['stalled']} | "
                    f"MetaDL: {stats['metadl']}")
        logging.info(f"   Errors: {stats['error']} | Paused: {stats['paused']}")
        logging.info(f"   Monitored: {len(self.torrent_states)}")
        
        # Session statistics
        session_time = (time.time() - self.stats["session_started"]) / 3600
        if session_time > 0:
            logging.info(f"📊 Session Stats: {self.stats['torrents_removed']} removed, "
                        f"{self.stats['space_freed'] / (1024**3):.2f} GB freed "
                        f"in {session_time:.1f} hours")
    
    def _clean_old_states(self, current_torrents: List[Dict]):
        """Clean states for torrents no longer present"""
        current_hashes = {t["hash"] for t in current_torrents}
        old_states = [h for h in self.torrent_states if h not in current_hashes]
        
        for h in old_states:
            del self.torrent_states[h]
        
        if old_states:
            logging.info(f"🧹 Cleaned {len(old_states)} obsolete state(s)")
    
    def run(self):
        """Main loop"""
        check_interval = self.config["thresholds"]["check_interval"]
        
        logging.info(f"🧹 TorrentJanitor v{__version__} started")
        logging.info(f"⏰ Checking every {check_interval // 60} minutes")
        logging.info(f"📁 State directory: {self.work_dir}")
        
        while True:
            try:
                self.clean_torrents()
                
                # Log rotation if needed
                if self.log_file.exists():
                    max_size = self.config.get("logging", {}).get("max_file_size_mb", 10) * 1024 * 1024
                    if self.log_file.stat().st_size > max_size:
                        self._rotate_log()
                
            except KeyboardInterrupt:
                logging.info("⛔ Shutdown requested by user")
                break
            except Exception as e:
                logging.error(f"❌ Unexpected error: {e}", exc_info=True)
            
            logging.info(f"💤 Next check in {check_interval // 60} minutes")
            logging.info("=" * 60)
            time.sleep(check_interval)
    
    def _rotate_log(self):
        """Rotate log file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.log_file.parent / f"{self.log_file.stem}_{timestamp}.log"
            self.log_file.rename(backup)
            logging.info("📝 Log file rotated")
            
            # Clean old logs
            max_files = self.config.get("logging", {}).get("max_files", 5)
            log_files = sorted(self.log_file.parent.glob(f"{self.log_file.stem}_*.log"))
            if len(log_files) > max_files:
                for old_log in log_files[:-max_files]:
                    old_log.unlink()
                    logging.info(f"🗑️  Deleted old log: {old_log.name}")
        except Exception as e:
            logging.error(f"Log rotation error: {e}")

def load_config(config_file: Optional[str] = None) -> Dict:
    """Load configuration from file or use defaults"""
    default_config = {
        "qbittorrent": {
            "host": os.getenv("QB_HOST", "localhost"),
            "port": int(os.getenv("QB_PORT", "8080")),
            "username": os.getenv("QB_USERNAME", "admin"),
            "password": os.getenv("QB_PASSWORD", "adminadmin"),
            "timeout": 30,
            "verify_ssl": True
        },
        "thresholds": {
            "max_queue_time": 172800,      # 48 hours
            "max_meta_time": 3600,          # 1 hour
            "min_torrent_age": 86400,       # 24 hours
            "grace_checks": 3,              
            "check_interval": 1800,         # 30 minutes
            "min_progress_protect": 5,      # Protect torrents > 5% progress
            "min_download_speed": 1024,     # 1 KB/s
            "min_seeds_required": 1,
            "max_seed_time": 604800         # 7 days
        },
        "rules": {
            "remove_errors": True,
            "remove_stalled": True,
            "remove_metadata_timeout": True,
            "remove_no_activity": True,
            "remove_queue_timeout": True,
            "remove_low_ratio": False,
            "protect_seeding": True,
            "protect_private_trackers": False,
            "min_seed_ratio": 1.0,
            "max_torrent_size_gb": 0
        },
        "categories": {
            "protected": [],
            "auto_remove": [],
            "private_trackers": []
        },
        "logging": {
            "level": "INFO",
            "max_file_size_mb": 10,
            "max_files": 5,
            "format": "%(asctime)s - %(levelname)s - %(message)s"
        },
        "paths": {
            "work_dir": os.getenv("WORK_DIR", "/tmp/torrentjanitor"),
            "state_file": "torrent_states.json",
            "log_file": "torrentjanitor.log",
            "stats_file": "statistics.json"
        }
    }
    
    # Try loading config from file
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                # Deep merge configurations
                def deep_merge(base, override):
                    for key, value in override.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            deep_merge(base[key], value)
                        else:
                            base[key] = value
                deep_merge(default_config, file_config)
                logging.info(f"✓ Configuration loaded from {config_file}")
        except Exception as e:
            logging.warning(f"⚠️  Could not load config file: {e}, using defaults")
    
    return default_config

def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description=f"TorrentJanitor v{__version__} - Automated qBittorrent Cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run with default settings
  %(prog)s --config my.json   # Use custom config file
  %(prog)s --dry-run --once   # Test mode, run once
  %(prog)s --verbose          # Enable debug logging
  
Environment Variables:
  QB_HOST       qBittorrent host (default: localhost)
  QB_PORT       qBittorrent port (default: 8080)
  QB_USERNAME   qBittorrent username
  QB_PASSWORD   qBittorrent password
  WORK_DIR      Working directory for state files
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate operations without making changes"
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help="Run once instead of continuous loop"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose debug output"
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Apply command-line overrides
    if args.dry_run:
        print("🔍 DRY-RUN MODE: No changes will be made")
        config["dry_run"] = True
    
    if args.verbose:
        config["logging"]["level"] = "DEBUG"
    
    # Create and run janitor
    janitor = TorrentJanitor(config)
    
    try:
        if args.once:
            janitor.clean_torrents()
        else:
            janitor.run()
    except KeyboardInterrupt:
        print("\n⛔ Shutdown requested")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()