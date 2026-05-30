"""WebScraper collector — probes target website for security signals.

Uses Bright Data Web Unlocker for page content analysis (robots.txt,
security.txt) and supplements with direct SSL certificate and security
header inspection where the Web Unlocker doesn't expose raw protocol data.
"""

import logging
import ssl
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)

# Standard security headers to check
SECURITY_HEADERS = {
    "Content-Security-Policy": "Helps prevent XSS and data injection attacks",
    "Strict-Transport-Security": "Enforces HTTPS connections",
    "X-Frame-Options": "Prevents clickjacking attacks",
    "X-Content-Type-Options": "Prevents MIME type sniffing",
    "Referrer-Policy": "Controls referrer information leakage",
}

COMMON_PORTS = [80, 443, 8080, 8443]


class WebScraperFinding:
    """Finding from direct website probing."""

    def __init__(
        self,
        source_url: str,
        title: str,
        description: str,
        severity: str = "info",
        finding_type: str = "vulnerability",
        check_type: str = "general",
        raw_data: Optional[str] = None,
    ):
        self.source_type = "web_scraper"
        self.source_url = source_url
        self.title = title
        self.description = description
        self.severity = severity
        self.finding_type = finding_type
        self.check_type = check_type
        self.raw_data = raw_data
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "check_type": self.check_type,
            "raw_data": self.raw_data,
            "timestamp": self.timestamp.isoformat(),
        }


class WebScraper:
    """Probes a target website for security-relevant signals.

    Checks performed:
      1. Well-known security paths (robots.txt, security.txt)
      2. Security headers (CSP, HSTS, X-Frame-Options, etc.)
      3. SSL certificate validity and expiry
      4. Server information disclosure
      5. Page accessibility through Bright Data proxy
    """

    def __init__(self, target_url: str):
        self.target_url = target_url.rstrip("/")
        try:
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            self.hostname = parsed.hostname or ""
            self.port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except Exception:
            self.hostname = target_url
            self.port = 443
        self.scheme = "https" if "https" in target_url else "http"

    async def collect(self) -> List[WebScraperFinding]:
        """Run all checks and return findings."""
        findings: List[WebScraperFinding] = []

        checks = [
            self._check_wellknown_paths(),
            self._check_security_headers(),
            self._check_ssl_cert(),
            self._check_server_info(),
            self._check_page_access(),
            self._check_with_browser(),
        ]

        for check in checks:
            try:
                result = await check
                findings.extend(result)
            except Exception as e:
                logger.warning(f"WebScraper check failed: {e}")

        return findings

    async def _fetch_via_brightdata(self, path: str) -> Optional[str]:
        """Fetch a URL path via Bright Data Web Unlocker."""
        url = f"{self.scheme}://{self.hostname}{path}"
        try:
            content = await brightdata.web_unlocker_get(url, render=False)
            if content and len(content.strip()) > 0:
                return content
        except Exception as e:
            logger.debug(f"Bright Data fetch failed for {url}: {e}")
        return None

    # ── Check 1: Well-known security paths ──────────────────────── #

    async def _check_wellknown_paths(self) -> List[WebScraperFinding]:
        """Check /.well-known/security.txt, /robots.txt, /sitemap.xml."""
        findings: List[WebScraperFinding] = []

        # security.txt
        content = await self._fetch_via_brightdata("/.well-known/security.txt")
        if content is None:
            findings.append(WebScraperFinding(
                source_url=f"{self.scheme}://{self.hostname}/.well-known/security.txt",
                title="No security.txt found — no responsible disclosure policy",
                description=(
                    f"The site {self.hostname} does not publish a security.txt file at the "
                    "standard /.well-known/security.txt path. This makes it harder for "
                    "security researchers to report vulnerabilities responsibly."
                ),
                severity="medium",
                check_type="well-known",
            ))
        else:
            has_contact = "Contact" in content or "contact" in content.lower()[:500]
            findings.append(WebScraperFinding(
                source_url=f"{self.scheme}://{self.hostname}/.well-known/security.txt",
                title="Security.txt found with security disclosure policy",
                description=(
                    f"Security researchers can report vulnerabilities via the published "
                    f"policy{' which includes contact information' if has_contact else ''}."
                ),
                severity="info",
                check_type="well-known",
                raw_data=content[:500],
            ))

        # robots.txt
        content = await self._fetch_via_brightdata("/robots.txt")
        if content is not None:
            disallowed = [
                line.split(":")[1].strip()
                for line in content.split("\n")
                if line.lower().startswith("disallow") and ":" in line
            ]
            sensitive = [p for p in disallowed if any(
                kw in p.lower() for kw in ["admin", "internal", "config", "backup", "wp-", "login", "api"]
            )]
            if sensitive:
                findings.append(WebScraperFinding(
                    source_url=f"{self.scheme}://{self.hostname}/robots.txt",
                    title=f"Robots.txt exposes {len(sensitive)} sensitive disallowed paths",
                    description=(
                        f"Robots.txt disallows crawling of: {', '.join(sensitive[:5])}. "
                        "While robots.txt is a crawl directive (not a security control), "
                        "these paths are now publicly enumerated."
                    ),
                    severity="low",
                    check_type="well-known",
                    raw_data="\n".join(disallowed[:10]),
                ))
            else:
                findings.append(WebScraperFinding(
                    source_url=f"{self.scheme}://{self.hostname}/robots.txt",
                    title="Robots.txt found — no sensitive paths exposed",
                    description=f"Robots.txt is present with {len(disallowed)} disallowed paths, none appear sensitive.",
                    severity="info",
                    check_type="well-known",
                ))
        else:
            findings.append(WebScraperFinding(
                source_url=f"{self.scheme}://{self.hostname}/robots.txt",
                title="No robots.txt found",
                description="The site does not publish a robots.txt file. This is informational only.",
                severity="info",
                check_type="well-known",
            ))

        return findings

    # ── Check 2: Security headers ───────────────────────────────── #

    async def _check_security_headers(self) -> List[WebScraperFinding]:
        """Check HTTP response security headers."""
        findings: List[WebScraperFinding] = []

        try:
            async with httpx.AsyncClient(
                verify=False,
                timeout=10.0,
                follow_redirects=True,
            ) as client:
                url = f"{self.scheme}://{self.hostname}"
                response = await client.get(url)

                headers = {k.lower(): v for k, v in response.headers.items()}

                for header, purpose in SECURITY_HEADERS.items():
                    if header.lower() not in headers:
                        findings.append(WebScraperFinding(
                            source_url=url,
                            title=f"Missing {header} security header",
                            description=(
                                f"The {header} header is not set on responses from {self.hostname}. "
                                f"{purpose}. Adding this header improves the site's security posture."
                            ),
                            severity="medium",
                            check_type="headers",
                        ))

                # X-XSS-Protection is deprecated but still good to note
                if "x-xss-protection" not in headers:
                    findings.append(WebScraperFinding(
                        source_url=url,
                        title="Missing X-XSS-Protection header",
                        description=(
                            f"X-XSS-Protection header is not set. Note this header is deprecated "
                            f"in modern browsers in favor of CSP."
                        ),
                        severity="low",
                        check_type="headers",
                    ))

        except httpx.ConnectError:
            findings.append(WebScraperFinding(
                source_url=f"{self.scheme}://{self.hostname}",
                title=f"Cannot connect to {self.hostname} for header inspection",
                description=(
                    f"Failed to establish an HTTP connection to {self.hostname} "
                    f"to inspect security headers."
                ),
                severity="high",
                check_type="headers",
            ))
        except Exception as e:
            logger.warning(f"Header check failed for {self.hostname}: {e}")

        return findings

    # ── Check 3: SSL certificate ────────────────────────────────── #

    async def _check_ssl_cert(self) -> List[WebScraperFinding]:
        """Inspect SSL/TLS certificate for expiry and validity."""
        findings: List[WebScraperFinding] = []

        if self.scheme != "https":
            return findings  # skip SSL check for HTTP sites

        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            reader, writer = await asyncio_open_connection(
                self.hostname, 443, ssl=context,
            )
            sock = writer.transport.get_extra_info("ssl_object")
            if sock:
                cert = sock.getpeercert()
                if cert:
                    # Check expiry
                    not_after = cert.get("notAfter", "")
                    if not_after:
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        remaining = (expiry - datetime.now(timezone.utc)).days
                        issuer = dict(x[0] for x in cert.get("issuer", []))
                        subject = dict(x[0] for x in cert.get("subject", []))
                        cn = subject.get("commonName", "unknown")

                        if remaining <= 0:
                            findings.append(WebScraperFinding(
                                source_url=f"https://{self.hostname}",
                                title="SSL certificate has expired",
                                description=(
                                    f"The SSL certificate for {self.hostname} (CN: {cn}) "
                                    f"expired {abs(remaining)} days ago. This will cause "
                                    f"browser security warnings and erode user trust."
                                ),
                                severity="critical",
                                check_type="ssl",
                            ))
                        elif remaining <= 7:
                            findings.append(WebScraperFinding(
                                source_url=f"https://{self.hostname}",
                                title=f"SSL certificate expiring in {remaining} days",
                                description=(
                                    f"The SSL certificate for {self.hostname} (CN: {cn}) "
                                    f"expires in {remaining} days on {expiry.strftime('%Y-%m-%d')}. "
                                    f"Issuer: {issuer.get('organizationName', 'Unknown')}. "
                                    f"Renewal should be scheduled immediately."
                                ),
                                severity="high",
                                check_type="ssl",
                            ))
                        elif remaining <= 30:
                            findings.append(WebScraperFinding(
                                source_url=f"https://{self.hostname}",
                                title=f"SSL certificate expiring in {remaining} days",
                                description=(
                                    f"The SSL certificate for {self.hostname} expires "
                                    f"in {remaining} days on {expiry.strftime('%Y-%m-%d')}. "
                                    f"Issuer: {issuer.get('organizationName', 'Unknown')}."
                                ),
                                severity="medium",
                                check_type="ssl",
                            ))
                        else:
                            findings.append(WebScraperFinding(
                                source_url=f"https://{self.hostname}",
                                title="SSL certificate valid and healthy",
                                description=(
                                    f"SSL certificate for {self.hostname} (CN: {cn}) "
                                    f"is valid for {remaining} more days. "
                                    f"Issuer: {issuer.get('organizationName', 'Unknown')}."
                                ),
                                severity="info",
                                check_type="ssl",
                            ))

                        # Check for self-signed
                        if issuer.get("organizationName") == subject.get("organizationName"):
                            findings.append(WebScraperFinding(
                                source_url=f"https://{self.hostname}",
                                title="Self-signed SSL certificate detected",
                                description=(
                                    f"The SSL certificate for {self.hostname} is self-signed "
                                    f"(issuer matches subject). Self-signed certificates are not "
                                    f"trusted by browsers and will trigger security warnings."
                                ),
                                severity="high",
                                check_type="ssl",
                            ))
                else:
                    findings.append(WebScraperFinding(
                        source_url=f"https://{self.hostname}",
                        title="SSL certificate details unavailable",
                        description="Connected over SSL but could not retrieve certificate details.",
                        severity="low",
                        check_type="ssl",
                    ))

            writer.close()
            await writer.wait_closed()

        except ssl.SSLError as e:
            findings.append(WebScraperFinding(
                source_url=f"https://{self.hostname}",
                title=f"SSL connection error: {e}",
                description=f"SSL handshake failed for {self.hostname}: {e}. The certificate may be invalid or self-signed.",
                severity="high",
                check_type="ssl",
            ))
        except (OSError, socket.gaierror) as e:
            findings.append(WebScraperFinding(
                source_url=f"https://{self.hostname}",
                title=f"Cannot establish SSL connection to {self.hostname}",
                description=f"Failed to connect for SSL inspection: {e}",
                severity="high",
                check_type="ssl",
            ))
        except Exception as e:
            logger.warning(f"SSL check failed for {self.hostname}: {e}")

        return findings

    # ── Check 4: Server info disclosure ─────────────────────────── #

    async def _check_server_info(self) -> List[WebScraperFinding]:
        """Check for information disclosure in Server / X-Powered-By headers."""
        findings: List[WebScraperFinding] = []

        try:
            async with httpx.AsyncClient(
                verify=False,
                timeout=10.0,
                follow_redirects=True,
            ) as client:
                url = f"{self.scheme}://{self.hostname}"
                response = await client.get(url)

                server = response.headers.get("server", "").strip()
                powered_by = response.headers.get("x-powered-by", "").strip()

                if server:
                    findings.append(WebScraperFinding(
                        source_url=url,
                        title=f"Server header discloses version info: {server}",
                        description=(
                            f"The Server header reveals \"{server}\". This exposes the web "
                            f"server type and version, which can help attackers target "
                            f"known vulnerabilities for that specific version."
                        ),
                        severity="low",
                        check_type="server_info",
                    ))

                if powered_by:
                    findings.append(WebScraperFinding(
                        source_url=url,
                        title=f"X-Powered-By header discloses: {powered_by}",
                        description=(
                            f"The X-Powered-By header reveals \"{powered_by}\", "
                            f"exposing the technology stack to potential attackers."
                        ),
                        severity="low",
                        check_type="server_info",
                    ))

        except Exception as e:
            logger.debug(f"Server info check failed for {self.hostname}: {e}")

        return findings

    # ── Check 5: Page accessibility ─────────────────────────────── #

    async def _check_page_access(self) -> List[WebScraperFinding]:
        """Check if the page is accessible via Bright Data Web Unlocker."""
        findings: List[WebScraperFinding] = []

        content = await self._fetch_via_brightdata("/")
        if content is None:
            findings.append(WebScraperFinding(
                source_url=self.target_url,
                title=f"Website unreachable via Bright Data proxy",
                description=(
                    f"Could not fetch {self.target_url} through the Bright Data Web Unlocker. "
                    f"This is a monitoring infrastructure note — the site may be blocking "
                    f"automated access, which is often a positive anti-bot signal."
                ),
                severity="low",
                check_type="accessibility",
            ))
        else:
            content_lower = content.lower()
            # Check for common security-relevant signals in the page content
            if "http://" in content_lower and "https://" in content_lower:
                findings.append(WebScraperFinding(
                    source_url=self.target_url,
                    title="Mixed content detected — page serves both HTTP and HTTPS resources",
                    description=(
                        f"The page at {self.target_url} contains references to both HTTP "
                        f"and HTTPS resources. Mixed content can trigger browser security "
                        f"warnings and expose users to MITM attacks."
                    ),
                    severity="medium",
                    check_type="accessibility",
                ))

            if any(term in content_lower for term in ["not secure", "your connection is not private"]):
                findings.append(WebScraperFinding(
                    source_url=self.target_url,
                    title="Page content indicates security warning to users",
                    description=(
                        f"The page content contains phrases like \"not secure\" or "
                        f"\"your connection is not private\", suggesting users may see "
                        f"browser security warnings."
                    ),
                    severity="high",
                    check_type="accessibility",
                ))

            findings.append(WebScraperFinding(
                source_url=self.target_url,
                title=f"Website accessible via Bright Data proxy",
                description=(
                    f"Successfully fetched {self.target_url} through Bright Data Web Unlocker "
                    f"({len(content)} bytes returned). The site is reachable and responsive."
                ),
                severity="info",
                check_type="accessibility",
            ))

        return findings

    # ── Check 6: Scraping Browser analysis ────────────────────────── #

    async def _check_with_browser(self) -> List[WebScraperFinding]:
        """Launch Scraping Browser to analyze JS-rendered page content.

        Uses Bright Data Scraping Browser (`bdata browser open`) to get
        the full accessibility tree of JS-heavy pages, detecting third-party
        scripts and client-side security signals.
        """
        findings: List[WebScraperFinding] = []

        try:
            snapshot = await brightdata.scraping_browser_navigate(self.target_url)
            if not snapshot or len(snapshot.strip()) < 50:
                findings.append(WebScraperFinding(
                    source_url=self.target_url,
                    title="Scraping Browser could not render page content",
                    description=(
                        f"The Bright Data Scraping Browser was unable to render "
                        f"{self.target_url}. The page may be too heavy or blocking headless browsers."
                    ),
                    severity="low",
                    check_type="browser",
                ))
                return findings

            content_lower = snapshot.lower()

            # Count third-party scripts
            import re
            script_srcs = re.findall(r'<script[^>]*src=["\'](https?://[^"\']+)["\']', snapshot)
            third_party_domains = set()
            for src in script_srcs:
                from urllib.parse import urlparse
                domain = urlparse(src).hostname or ""
                if domain and domain not in self.hostname:
                    third_party_domains.add(domain)

            if third_party_domains:
                findings.append(WebScraperFinding(
                    source_url=self.target_url,
                    title=f"Browser loaded {len(third_party_domains)} third-party script domains",
                    description=(
                        f"The Scraping Browser detected {len(script_srcs)} total scripts, "
                        f"including {len(third_party_domains)} third-party domain(s): "
                        f"{', '.join(sorted(third_party_domains)[:6])}. "
                        f"Third-party scripts can introduce XSS vectors and data leakage risks."
                    ),
                    severity="medium",
                    check_type="browser",
                    raw_data="\n".join(sorted(third_party_domains)),
                ))

            # Check for inline JavaScript
            inline_scripts = re.findall(
                r'<script[^>]*>([^<]*(?:function|eval|setTimeout|setInterval|onclick|onload)[^<]*?)</script>',
                snapshot[:10000],
            )
            if inline_scripts:
                findings.append(WebScraperFinding(
                    source_url=self.target_url,
                    title=f"Browser found {len(inline_scripts)} inline scripts with executable JS",
                    description=(
                        f"The Scraping Browser detected {len(inline_scripts)} inline "
                        f"<script> blocks containing JavaScript (function definitions, "
                        f"event handlers, etc.). Inline JS makes CSP enforcement harder."
                    ),
                    severity="low",
                    check_type="browser",
                ))

            # Check for mixed content in rendered DOM
            if "http://" in content_lower and "https://" in content_lower:
                http_refs = re.findall(r'src=["\']http://[^"\']+', content_lower)
                if http_refs:
                    findings.append(WebScraperFinding(
                        source_url=self.target_url,
                        title=f"Browser detected {len(http_refs)} HTTP resource references",
                        description=(
                            f"The rendered page loads {len(http_refs)} resource(s) over "
                            f"plain HTTP. Mixed content can trigger browser security warnings."
                        ),
                        severity="medium",
                        check_type="browser",
                    ))

            # Snapshot length indicator
            findings.append(WebScraperFinding(
                source_url=self.target_url,
                title=f"Scraping Browser rendered {len(snapshot)} characters of content",
                description=(
                    f"The Bright Data Scraping Browser successfully loaded and rendered "
                    f"{self.target_url}. The page produces {len(snapshot)} characters of "
                    f"rendered DOM (accessibility tree)."
                ),
                severity="info",
                check_type="browser",
            ))

        except Exception as e:
            logger.warning(f"Scraping Browser check failed for {self.target_url}: {e}")
            findings.append(WebScraperFinding(
                source_url=self.target_url,
                title="Scraping Browser analysis failed",
                description=f"The browser analysis encountered an error: {e}",
                severity="info",
                check_type="browser",
            ))

        return findings


async def asyncio_open_connection(host: str, port: int, ssl: ssl.SSLContext):
    """Wrapper around asyncio.open_connection for SSL inspection."""
    import asyncio
    return await asyncio.open_connection(host, port, ssl=ssl)
