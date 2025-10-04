#!/usr/bin/env python3
"""
Payment Gateway Proxy Monitor - Textual TUI Interface

MSCHF Style Edition: "Welcome to Convenience, where nothing is Convenient"
"""

import os
import yaml
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, Input,
    TextArea, TabbedContent, TabPane, DataTable, RichLog
)
from textual import on
from dotenv import load_dotenv, set_key

load_dotenv()


class ProxyMonitor(App):
    """Textual TUI application for monitoring the payment gateway proxy - MSCHF Edition"""

    CSS = """
    Screen {
        background: black;
    }

    Header {
        background: white;
        color: black;
    }

    Footer {
        background: white;
        color: black;
    }

    #mschf-banner {
        height: 3;
        background: white;
        color: black;
        text-align: center;
        text-style: bold;
    }

    .status-text {
        color: white;
        text-style: bold;
        text-align: center;
        height: 3;
    }

    Button {
        width: 1fr;
        background: white;
        color: black;
        margin: 1;
    }

    Button:hover {
        background: black;
        color: white;
        border: solid white;
    }

    .stat-card {
        border: solid white;
        margin: 1;
        padding: 1;
    }

    .stat-title {
        color: white;
        text-style: bold;
    }

    .stat-number {
        color: white;
        text-style: bold;
    }

    Input {
        background: black;
        border: solid white;
        color: white;
        margin: 1;
    }

    .config-label {
        color: white;
        text-style: bold;
        margin: 1;
    }

    DataTable {
        border: solid white;
        margin: 1;
    }

    TextArea {
        border: solid white;
        margin: 1;
    }

    RichLog {
        border: solid white;
        margin: 1;
    }

    Tab {
        background: black;
        color: white;
    }

    Tab.-active {
        background: white;
        color: black;
    }

    .status-msg {
        color: white;
        margin: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_tab('control')", "Control"),
        ("2", "switch_tab('logs')", "Logs"),
        ("3", "switch_tab('settings')", "Settings"),
        ("4", "switch_tab('routes')", "Routes"),
    ]

    def __init__(self):
        super().__init__()
        self.log_file = self._get_latest_log_file()
        self.env_file = Path(".env")
        self.routing_config_file = Path("routing_config.yaml")
        self.proxy_process: Optional[subprocess.Popen] = None

    def _get_latest_log_file(self) -> Optional[Path]:
        """Find the latest proxy log file"""
        log_files = list(Path(".").glob("proxy_*.log"))
        if log_files:
            return max(log_files, key=lambda p: p.stat().st_mtime)
        return None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True)

        # MSCHF Banner
        yield Static(
            "Welcome to Convenience, where nothing is Convenient",
            id="mschf-banner"
        )

        with TabbedContent(initial="control"):
            # Control Tab
            with TabPane("Control", id="control"):
                yield Static("■ STOPPED", classes="status-text", id="status-text")

                with Horizontal():
                    yield Button("▶ START", id="start-btn")
                    yield Button("■ STOP", id="stop-btn")
                    yield Button("↻ RESTART", id="restart-btn")

                with Horizontal():
                    with Vertical(classes="stat-card"):
                        yield Static("RECEIVED", classes="stat-title")
                        yield Static("0", id="stat-received", classes="stat-number")

                    with Vertical(classes="stat-card"):
                        yield Static("SENT", classes="stat-title")
                        yield Static("0", id="stat-sent", classes="stat-number")

                    with Vertical(classes="stat-card"):
                        yield Static("ERRORS", classes="stat-title")
                        yield Static("0", id="stat-errors", classes="stat-number")

            # Logs Tab
            with TabPane("Logs", id="logs"):
                yield RichLog(id="log-viewer", wrap=False, markup=True)

            # Settings Tab
            with TabPane("Settings", id="settings"):
                yield ScrollableContainer(
                    Label("WebSocket Server URL", classes="config-label"),
                    Input(
                        value=os.getenv("WS_SERVER_URL", ""),
                        placeholder="wss://server.com/ws",
                        id="ws-url-input"
                    ),
                    Label("WebSocket Token", classes="config-label"),
                    Input(
                        value=os.getenv("WS_TOKEN", ""),
                        placeholder="token",
                        id="ws-token-input",
                        password=True
                    ),
                    Label("Log Level", classes="config-label"),
                    Input(
                        value=os.getenv("LOG_LEVEL", "INFO"),
                        placeholder="INFO",
                        id="log-level-input"
                    ),
                    Button("SAVE SETTINGS", id="save-settings-btn"),
                    Static("", id="settings-status", classes="status-msg")
                )

            # Routes Tab
            with TabPane("Routes", id="routes"):
                with Vertical():
                    yield DataTable(id="routes-table")
                    with Horizontal():
                        yield Button("RELOAD ROUTES", id="reload-routes-btn")
                    yield Label("Edit routing_config.yaml", classes="config-label")
                    yield TextArea(
                        text=self._load_routing_config_text(),
                        language="yaml",
                        id="routing-editor"
                    )
                    yield Button("SAVE ROUTES", id="save-routes-btn")
                    yield Static("", id="routes-status", classes="status-msg")

        yield Footer()

    def _load_routing_config_text(self) -> str:
        """Load routing config file as text"""
        try:
            if self.routing_config_file.exists():
                return self.routing_config_file.read_text()
            return "# No routing config file found"
        except Exception as e:
            return f"# Error: {e}"

    def on_mount(self) -> None:
        """Called when app starts"""
        self.set_interval(3, self.update_stats)
        self.set_interval(2, self.update_logs)
        self.set_interval(1, self.check_proxy_status)
        self.load_routes_table()

    def check_proxy_status(self) -> None:
        """Check if proxy process is running"""
        status_widget = self.query_one("#status-text", Static)
        if self.proxy_process and self.proxy_process.poll() is None:
            status_widget.update("▶ RUNNING")
        else:
            status_widget.update("■ STOPPED")

    @on(Button.Pressed, "#start-btn")
    def start_proxy(self) -> None:
        """Start the proxy process"""
        if self.proxy_process and self.proxy_process.poll() is None:
            return

        try:
            self.proxy_process = subprocess.Popen(
                [sys.executable, "proxy.py"],
                cwd=Path.cwd()
            )
            self.set_timer(2, self._refresh_log_file)
        except Exception as e:
            self.query_one("#status-text", Static).update(f"ERROR: {e}")

    @on(Button.Pressed, "#stop-btn")
    def stop_proxy(self) -> None:
        """Stop the proxy process"""
        if self.proxy_process and self.proxy_process.poll() is None:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()
            self.proxy_process = None

    @on(Button.Pressed, "#restart-btn")
    def restart_proxy(self) -> None:
        """Restart the proxy process"""
        self.stop_proxy()
        self.set_timer(1, self.start_proxy)

    def _refresh_log_file(self) -> None:
        """Refresh log file reference"""
        self.log_file = self._get_latest_log_file()
        if hasattr(self, '_last_log_size'):
            self._last_log_size = 0

    def update_stats(self) -> None:
        """Update statistics from log file"""
        if not self.log_file or not self.log_file.exists():
            return

        try:
            content = self.log_file.read_text()

            received = len(re.findall(r'📥 RECEIVED from WS server:', content))
            sent = len(re.findall(r'📤 SENT back to WS server:', content))
            errors = len(re.findall(r'❌', content))

            self.query_one("#stat-received", Static).update(str(received))
            self.query_one("#stat-sent", Static).update(str(sent))
            self.query_one("#stat-errors", Static).update(str(errors))
        except:
            pass

    def update_logs(self) -> None:
        """Update log viewer with new entries"""
        if not self.log_file or not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()

            if not hasattr(self, '_last_log_size'):
                self._last_log_size = 0

            current_size = len(lines)
            if current_size != self._last_log_size:
                log_widget = self.query_one("#log-viewer", RichLog)
                log_widget.clear()

                # Show last 100 lines
                recent = lines[-100:] if len(lines) > 100 else lines

                for line in recent:
                    if '📥 RECEIVED' in line or '📤 SENT' in line:
                        log_widget.write(f"[bold white]{line.rstrip()}[/bold white]")
                    elif '➡️' in line or '🏷️' in line:
                        log_widget.write(f"[white]{line.rstrip()}[/white]")
                    elif '❌' in line or 'ERROR' in line:
                        log_widget.write(f"[bold white]{line.rstrip()}[/bold white]")
                    elif '✅' in line:
                        log_widget.write(f"[white]{line.rstrip()}[/white]")
                    else:
                        log_widget.write(f"[dim white]{line.rstrip()}[/dim white]")

                self._last_log_size = current_size
        except:
            pass

    def load_routes_table(self) -> None:
        """Load routes into the table"""
        table = self.query_one("#routes-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Type", "URL", "Timeout")

        try:
            if self.routing_config_file.exists():
                with open(self.routing_config_file, 'r') as f:
                    config = yaml.safe_load(f)

                for op_type, route in config.get('routes', {}).items():
                    table.add_row(
                        op_type,
                        route.get('url', 'N/A'),
                        str(route.get('timeout', 'N/A'))
                    )

                if 'default' in config:
                    table.add_row(
                        "[DEFAULT]",
                        config['default'].get('url', 'N/A'),
                        str(config['default'].get('timeout', 'N/A'))
                    )
        except Exception as e:
            table.add_row("Error", str(e), "")

    @on(Button.Pressed, "#save-settings-btn")
    def save_settings(self) -> None:
        """Save settings to .env file"""
        try:
            ws_url = self.query_one("#ws-url-input", Input).value
            ws_token = self.query_one("#ws-token-input", Input).value
            log_level = self.query_one("#log-level-input", Input).value

            if self.env_file.exists():
                set_key(self.env_file, "WS_SERVER_URL", ws_url)
                set_key(self.env_file, "WS_TOKEN", ws_token)
                set_key(self.env_file, "LOG_LEVEL", log_level)
                self.query_one("#settings-status", Static).update("✅ Saved! Restart proxy.")
            else:
                self.query_one("#settings-status", Static).update("❌ .env not found")
        except Exception as e:
            self.query_one("#settings-status", Static).update(f"❌ Error: {e}")

    @on(Button.Pressed, "#save-routes-btn")
    def save_routes(self) -> None:
        """Save routing config from editor"""
        try:
            content = self.query_one("#routing-editor", TextArea).text
            yaml.safe_load(content)
            self.routing_config_file.write_text(content)
            self.load_routes_table()
            self.query_one("#routes-status", Static).update("✅ Saved! Restart proxy.")
        except yaml.YAMLError as e:
            self.query_one("#routes-status", Static).update(f"❌ Invalid YAML: {e}")
        except Exception as e:
            self.query_one("#routes-status", Static).update(f"❌ Error: {e}")

    @on(Button.Pressed, "#reload-routes-btn")
    def reload_routes_table(self) -> None:
        """Reload routes table"""
        self.load_routes_table()

    def action_switch_tab(self, tab: str) -> None:
        """Switch to specific tab"""
        self.query_one(TabbedContent).active = tab

    def on_unmount(self) -> None:
        """Cleanup when app closes"""
        if self.proxy_process and self.proxy_process.poll() is None:
            self.proxy_process.terminate()
            try:
                self.proxy_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()


if __name__ == "__main__":
    app = ProxyMonitor()
    app.run()
