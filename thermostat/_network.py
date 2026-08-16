"""Pin outbound HTTP to IPv4.

NOAA publishes AAAA (IPv6) records for www.ncei.noaa.gov whose endpoints do not
accept connections.  As of 2026-08-02 none of the six advertised addresses
(2610:20:8040:2::167/168/171/172/177/178) answer ICMP or accept TCP on port 443,
while all six IPv4 addresses (205.167.25.167/168/171/172/177/178) serve the Data
Access API normally.

getaddrinfo sorts IPv6 ahead of IPv4 on dual-stack hosts (RFC 6724), so every
NCEI request from such a host is attempted against a dead endpoint first.  Hosts
with no IPv6 route fail immediately with [Errno 101] ENETUNREACH; hosts whose
IPv6 traffic is blackholed hang for roughly two minutes per address instead.

eeweather's ISD fetch (eeweather.access_api.make_api_request) is wrapped in
@retry(tries=3) and calls requests.get with no timeout, so this surfaces as:

    HTTPSConnectionPool(host='www.ncei.noaa.gov', port=443): Max retries
    exceeded with url: /access/services/data/v1?dataTypes=TMP&dataset=...

The consequence is not limited to failed runs.  When the fetch fails, the
affected hours are left as NaN; days with more than two missing hours are then
dropped from the core day set by Thermostat._get_core_day_sets, so metrics are
computed over a shorter period with nothing in the output to indicate it.

Pinning the address family to AF_INET restores normal operation.  This is a
workaround for a defect on NOAA's side, not a permanent change.  Once NOAA's
IPv6 endpoints respond, set THERMOSTAT_ALLOW_IPV6=1 to restore dual-stack
resolution without modifying this package, then remove this module.
"""
import logging
import os
import socket

logger = logging.getLogger(__name__)

#: Set to 1/true/yes to skip the pin and use normal dual-stack resolution.
ALLOW_IPV6_ENV_VAR = "THERMOSTAT_ALLOW_IPV6"

_applied = False


def _opted_out():
    return os.environ.get(ALLOW_IPV6_ENV_VAR, "").strip().lower() in (
        "1", "true", "yes", "on")


def force_ipv4():
    """Make urllib3 resolve hostnames to IPv4 addresses only.

    Applies process-wide to every connection made through requests/urllib3, and
    is safe to call more than once.  Returns True if the pin is now in effect.
    """
    global _applied

    if _applied:
        return True

    if _opted_out():
        logger.debug(
            "%s is set; leaving dual-stack name resolution in place",
            ALLOW_IPV6_ENV_VAR)
        return False

    try:
        import urllib3.util.connection as urllib3_connection
    except ImportError:
        # urllib3 is absent during initial setup, before dependencies install.
        return False

    # urllib3's create_connection looks allowed_gai_family up in its own module
    # globals on every call, so replacing the attribute is enough; no connection
    # pool or session needs to be rebuilt.
    urllib3_connection.allowed_gai_family = lambda: socket.AF_INET
    _applied = True
    logger.debug(
        "Pinned outbound HTTP to IPv4 (NOAA IPv6 endpoints unreachable); "
        "set %s=1 to disable.", ALLOW_IPV6_ENV_VAR)
    return True
