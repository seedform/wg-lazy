"""Default app parameters."""

CONFIG_DIR = "/etc/wireguard"

# TODO: normalize names
WG_INTERFACE = "wg0"
INTERFACE_ADDRESS = "10.168.0.1/24"
LISTEN_PORT = 51820
POST_UP_SCRIPT_PATH = "/etc/wireguard/wg-lazy/post-up.sh"
POST_DOWN_SCRIPT_PATH = "/etc/wireguard/wg-lazy/post-down.sh"

ENDPOINT = "127.0.0.1:51820"
DNS = "1.1.1.1"
OUTPUT_FORMAT = "qr"
