#!/usr/bin/env python3
"""
WebSocket Proxy Client for Payment Gateway

Connects local payment gateway to cloud WebSocket server.
Forwards JSON messages bidirectionally between WS server and local HTTP gateway.
"""

import asyncio
import websockets
import aiohttp
import json
import logging
import os
import sys
import signal
import yaml
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PaymentGatewayProxy:
    """
    WebSocket proxy client that bridges cloud server and local payment gateway.
    """

    def __init__(
        self,
        ws_url: str,
        ws_token: str,
        routing_config_path: str = "routing_config.yaml",
        log_level: str = "INFO"
    ):
        self.ws_url = ws_url
        self.ws_token = ws_token
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True

        # Load routing configuration
        self.routing_config = self._load_routing_config(routing_config_path)

        # Reconnection settings (exponential backoff)
        self.reconnect_delay = 1  # Start with 1 second
        self.reconnect_max_delay = 60  # Max 60 seconds
        self.reconnect_multiplier = 2

        # Setup logging
        log_file = f"proxy_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'reconnections': 0
        }

    def _load_routing_config(self, config_path: str) -> Dict[str, Any]:
        """Load routing configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except FileNotFoundError:
            raise Exception(f"Routing config file not found: {config_path}")
        except yaml.YAMLError as e:
            raise Exception(f"Invalid YAML in routing config: {e}")

    async def connect_to_server(self) -> bool:
        """Establish WebSocket connection to cloud server"""
        try:
            full_url = f"{self.ws_url}?token={self.ws_token}"
            self.logger.info(f"Connecting to WS server: {self.ws_url}")

            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    full_url,
                    ping_interval=20,
                    ping_timeout=10
                ),
                timeout=15.0
            )

            self.logger.info("✅ Connected to cloud server")
            # Reset reconnect delay on successful connection
            self.reconnect_delay = 1
            return True

        except asyncio.TimeoutError:
            self.logger.error("❌ Connection timeout")
            return False
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {type(e).__name__}: {e}")
            return False

    def _get_gateway_route(self, operation_type: str) -> Optional[Dict[str, Any]]:
        """
        Get gateway route configuration for given operation type

        Args:
            operation_type: Operation type from Header-Operation-Type

        Returns:
            Route config dict with 'url' and 'timeout' or None if not found
        """
        routes = self.routing_config.get('routes', {})

        # Try to find exact match
        if operation_type in routes:
            return routes[operation_type]

        # Try default route
        if 'default' in self.routing_config:
            return self.routing_config['default']

        # No route found
        return None

    async def send_to_gateway(
        self,
        message_data: Dict[str, Any],
        gateway_url: str,
        gateway_timeout: int
    ) -> Dict[str, Any]:
        """
        Forward message to local payment gateway via HTTP POST

        Args:
            message_data: JSON message (without routing headers)
            gateway_url: Target gateway URL
            gateway_timeout: Request timeout in seconds

        Returns:
            Response from gateway or error object
        """
        try:
            self.logger.info(f"➡️  Forwarding to gateway: {gateway_url}")
            self.logger.info(f"   Payload: {json.dumps(message_data, ensure_ascii=False)}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    gateway_url,
                    json=message_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=gateway_timeout)
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"✅ Gateway response: HTTP {response.status}")
                        self.logger.info(f"   Response: {json.dumps(result, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Gateway error: HTTP {response.status}")
                        self.logger.error(f"   Error: {error_text}")
                        return {
                            'status': 'error',
                            'error': 'http_error',
                            'message': f"HTTP {response.status}: {error_text}"
                        }

        except asyncio.TimeoutError:
            self.logger.error(f"⏱️ Gateway timeout after {gateway_timeout}s")
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'error': 'timeout',
                'message': f'Gateway timeout after {gateway_timeout}s'
            }
        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"❌ Cannot connect to gateway: {e}")
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'error': 'connection_refused',
                'message': f'Cannot connect to gateway: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"❌ Gateway error: {type(e).__name__}: {e}")
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'error': 'other',
                'message': str(e)
            }

    async def handle_message(self, message: str):
        """Handle incoming message from WS server"""
        try:
            # Parse JSON from WS server
            data = json.loads(message)

            self.logger.info("=" * 80)
            self.logger.info(f"📥 RECEIVED from WS server:")
            self.logger.info(f"   {json.dumps(data, ensure_ascii=False, indent=2)}")

            # Handle ping/pong
            if data.get('type') == 'ping':
                pong_response = {'type': 'pong'}
                await self.websocket.send(json.dumps(pong_response))
                self.logger.info(f"📤 SENT pong response")
                self.logger.info("=" * 80)
                return

            # Count only non-ping messages
            self.stats['messages_received'] += 1

            # Extract routing headers from headers object or top level
            headers = data.get('headers', {})
            kiosk_id = headers.get('header-kiosk-id') or data.get('Header-Kiosk-Id')
            operation_type = headers.get('header-operation-type') or data.get('Header-Operation-Type')

            self.logger.info(f"🏷️  Header-Kiosk-Id: {kiosk_id}")
            self.logger.info(f"🏷️  Header-Operation-Type: {operation_type}")

            # Check if operation type is present
            if not operation_type:
                error_response = {
                    'status': 'error',
                    'error': 'missing_header',
                    'message': 'Header-Operation-Type is required'
                }
                self.logger.error("❌ Missing Header-Operation-Type")
                await self.websocket.send(json.dumps(error_response))
                self.stats['messages_sent'] += 1
                return

            # Get route for operation type
            route = self._get_gateway_route(operation_type)

            if not route:
                error_response = {
                    'status': 'error',
                    'error': 'route_not_found',
                    'message': f'No route configured for operation type: {operation_type}'
                }
                self.logger.error(f"❌ Route not found for operation type: {operation_type}")
                await self.websocket.send(json.dumps(error_response))
                self.stats['messages_sent'] += 1
                self.stats['errors'] += 1
                return

            # Extract body for gateway (if present) or use full data without headers
            message_to_send = data.get('body', data.copy())

            # Remove routing headers if they're on top level
            if isinstance(message_to_send, dict):
                message_to_send.pop('Header-Kiosk-Id', None)
                message_to_send.pop('Header-Operation-Type', None)
                message_to_send.pop('headers', None)

            # Forward to gateway based on route
            response = await self.send_to_gateway(
                message_to_send,
                route['url'],
                route['timeout']
            )

            # Send response back to WS server (as-is)
            await self.websocket.send(json.dumps(response))
            self.stats['messages_sent'] += 1

            self.logger.info(f"📤 SENT back to WS server:")
            self.logger.info(f"   {json.dumps(response, ensure_ascii=False, indent=2)}")
            self.logger.info("=" * 80)

        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON from server: {e}")
            self.stats['errors'] += 1
            # Send error back to server
            error_response = {
                'status': 'error',
                'error': 'invalid_json',
                'message': f'Failed to parse JSON: {str(e)}'
            }
            try:
                await self.websocket.send(json.dumps(error_response))
            except:
                pass

        except Exception as e:
            self.logger.error(f"❌ Error handling message: {type(e).__name__}: {e}")
            self.stats['errors'] += 1

    async def receive_messages(self):
        """Receive and process messages from WS server"""
        try:
            async for message in self.websocket:
                if not self.running:
                    break
                await self.handle_message(message)

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("⚠️  WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"❌ Error receiving messages: {e}")

    def print_stats(self):
        """Print statistics"""
        self.logger.info("=" * 60)
        self.logger.info("📊 Proxy Statistics:")
        self.logger.info(f"   Messages received: {self.stats['messages_received']}")
        self.logger.info(f"   Messages sent: {self.stats['messages_sent']}")
        self.logger.info(f"   Errors: {self.stats['errors']}")
        self.logger.info(f"   Reconnections: {self.stats['reconnections']}")
        self.logger.info("=" * 60)

    async def run(self):
        """Main run loop with automatic reconnection and exponential backoff"""
        self.logger.info("🚀 Payment Gateway Proxy starting...")
        self.logger.info(f"   WS Server: {self.ws_url}")
        self.logger.info(f"   Routing config loaded with {len(self.routing_config.get('routes', {}))} routes")

        while self.running:
            try:
                if await self.connect_to_server():
                    # Connection successful, start receiving messages
                    await self.receive_messages()

                    # Connection lost, will reconnect
                    if self.running:
                        self.stats['reconnections'] += 1
                        self.logger.warning(
                            f"⚠️  Connection lost. Reconnecting in {self.reconnect_delay}s..."
                        )
                        await asyncio.sleep(self.reconnect_delay)

                        # Exponential backoff
                        self.reconnect_delay = min(
                            self.reconnect_delay * self.reconnect_multiplier,
                            self.reconnect_max_delay
                        )
                else:
                    # Connection failed
                    if self.running:
                        self.logger.error(
                            f"❌ Connection failed. Retrying in {self.reconnect_delay}s..."
                        )
                        await asyncio.sleep(self.reconnect_delay)

                        # Exponential backoff
                        self.reconnect_delay = min(
                            self.reconnect_delay * self.reconnect_multiplier,
                            self.reconnect_max_delay
                        )

            except KeyboardInterrupt:
                self.logger.info("⚠️  Interrupted by user")
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"❌ Unexpected error: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)

        # Cleanup
        if self.websocket:
            await self.websocket.close()

        self.print_stats()
        self.logger.info("👋 Payment Gateway Proxy stopped")

    def stop(self):
        """Stop the proxy gracefully"""
        self.logger.info("🛑 Stopping proxy...")
        self.running = False


def main():
    """Main entry point"""
    # Load configuration from environment
    ws_url = os.getenv('WS_SERVER_URL')
    ws_token = os.getenv('WS_TOKEN')
    routing_config_path = os.getenv('ROUTING_CONFIG_PATH', 'routing_config.yaml')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    # Validate required configuration
    if not all([ws_url, ws_token]):
        print("❌ Error: Missing required environment variables")
        print("Required: WS_SERVER_URL, WS_TOKEN")
        print("\nExample:")
        print('export WS_SERVER_URL="wss://your-server.railway.app/ws"')
        print('export WS_TOKEN="your_jwt_token"')
        print('export ROUTING_CONFIG_PATH="routing_config.yaml"  # Optional, default: routing_config.yaml')
        sys.exit(1)

    # Create proxy instance
    proxy = PaymentGatewayProxy(
        ws_url=ws_url,
        ws_token=ws_token,
        routing_config_path=routing_config_path,
        log_level=log_level
    )

    # Handle shutdown signals
    def signal_handler(sig, frame):
        print("\n⚠️  Received shutdown signal")
        proxy.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run proxy
    try:
        asyncio.run(proxy.run())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
