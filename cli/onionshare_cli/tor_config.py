"""Validation and torrc rendering for the upstream proxy used by bundled Tor."""

import ipaddress
import json


def upstream_proxy_config(settings):
    """Return torrc lines, or raise ValueError before starting Tor.

    This proxy is between Tor and the network. It is not OnionShare's
    connection to Tor's own SOCKS listener. External Tor is configured by
    its owner, so saved bundled-Tor proxy settings are ignored in that mode.
    """
    if settings.get("connection_type") != "bundled" or not settings.get(
        "proxy_enabled"
    ):
        return ""
    kind = settings.get("proxy_type")
    if kind not in ("socks4", "socks5", "http"):
        raise ValueError(
            "Choose SOCKS4, SOCKS5 or HTTP CONNECT for the upstream proxy."
        )
    address = settings.get("proxy_address").strip()
    if not address or any(c.isspace() or c in '/\\#"\x00' for c in address):
        raise ValueError(
            "Enter an upstream proxy hostname or IP address, without a URL scheme."
        )
    if ":" in address:
        try:
            address = "[" + str(ipaddress.IPv6Address(address.strip("[]"))) + "]"
        except ValueError:
            raise ValueError(
                "Enter the upstream proxy address and port in separate fields."
            ) from None
    port = settings.get("proxy_port")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Enter an upstream proxy port between 1 and 65535.")
    username = settings.get("proxy_username")
    password = settings.get("proxy_password")
    # SOCKS4 does not support this username/password authentication mechanism.
    if kind == "socks4":
        username = password = ""
    if bool(username) != bool(password):
        raise ValueError(
            "Provide both proxy username and password, or leave both empty."
        )
    for value in (username, password):
        if any(c in value for c in "\r\n\x00"):
            raise ValueError(
                "Proxy credentials cannot contain line breaks or NUL characters."
            )
    if kind == "socks5" and any(
        len(v.encode("utf-8")) > 255 for v in (username, password)
    ):
        raise ValueError("SOCKS5 credentials must each be at most 255 UTF-8 bytes.")
    if kind == "http" and ":" in username:
        raise ValueError("An HTTP proxy username cannot contain a colon.")
    directive = {
        "socks4": "Socks4Proxy",
        "socks5": "Socks5Proxy",
        "http": "HTTPSProxy",
    }[kind]
    lines = [f"{directive} {address}:{port}"]
    if username:
        # Quote values so spaces, quotes and '#' remain credentials, not torrc syntax.
        quote = lambda value: json.dumps(value, ensure_ascii=False)
        if kind == "http":
            lines.append(f"HTTPSProxyAuthenticator {quote(username + ':' + password)}")
        else:
            lines.extend(
                [
                    f"Socks5ProxyUsername {quote(username)}",
                    f"Socks5ProxyPassword {quote(password)}",
                ]
            )
    return "\n" + "\n".join(lines) + "\n"
