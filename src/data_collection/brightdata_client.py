"""Bright Data client abstraction layer.

Provides unified access to Bright Data products used by SentinelWatch
via the Bright Data CLI (`bdata`):

- Web Unlocker (scrape): `bdata scrape` — Bypass bot detection, CAPTCHAs, geo-blocks
- SERP API (search): `bdata search` — Real-time structured search engine results
- Scraping Browser: `bdata browser` — Full browser automation for JS-heavy sites
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class BrightDataClientError(Exception):
    """Base exception for Bright Data client errors."""


class BrightDataClient:
    """Client for Bright Data's web data platform via the `bdata` CLI."""

    def __init__(self):
        self.api_key = settings.brightdata_api_key
        self.username = settings.brightdata_username

    async def _run_cli(self, *args: str, timeout: int = 60) -> str:
        """Run a `bdata` CLI command and return stdout.

        Args:
            *args: CLI arguments (e.g., 'scrape', 'https://...').
            timeout: Command timeout in seconds.

        Returns:
            Command stdout as string.
        """
        import sys
        bdata_cmd = "bdata.cmd" if sys.platform == "win32" else "bdata"
        cmd = [bdata_cmd, *args, "-k", self.api_key, "--json"]
        logger.debug(f"Running: {' '.join(cmd)}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "BDRIGHT_DATA_API_KEY": self.api_key},
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            if proc.returncode != 0:
                error_msg = stderr.decode().strip() or f"exit code {proc.returncode}"
                raise BrightDataClientError(
                    f"bdata CLI error: {error_msg}"
                )
            return stdout.decode()
        except asyncio.TimeoutError:
            raise BrightDataClientError(
                f"bdata command timed out after {timeout}s"
            )
        except FileNotFoundError:
            raise BrightDataClientError(
                "bdata CLI not found. Install it with: npm i -g @brightdata/cli"
            )

    # ------------------------------------------------------------------ #
    # Web Unlocker
    # ------------------------------------------------------------------ #

    async def web_unlocker_get(
        self, url: str, country: Optional[str] = None, render: bool = False
    ) -> str:
        """Retrieve page content bypassing bot detection and geo-blocks.

        Uses Bright Data Web Unlocker REST API with multi-tier fallback:
        1. Premium zone (if configured — for high-difficulty sites)
        2. Standard zone
        3. Mobile UA
        4. Scraping Browser (if WebSocket configured — strongest anti-detection)
        5. CLI subprocess

        For premium scraping, set BRIGHTDATA_PREMIUM_ZONE and/or
        BRIGHTDATA_BROWSER_WS env vars.

        Args:
            url: Target URL to retrieve.
            country: 2-letter country code for geo-targeting (e.g., 'us', 'gb').
            render: Whether to wait for JS rendering before returning.

        Returns:
            Page content as string.
        """
        logger.info(f"Web Unlocker fetching: {url}")

        # Tier 1: Premium zone (if configured — handles high-difficulty sites)
        premium_zone = settings.brightdata_premium_zone
        if premium_zone:
            try:
                result = await self._web_unlocker_rest_api(url, country="us", zone=premium_zone)
                if result:
                    logger.info(f"Premium zone success for {url}")
                    return result
            except Exception as e:
                logger.warning(f"Premium zone failed for {url}: {e}")

        # Tier 2: Standard zone
        try:
            result = await self._web_unlocker_rest_api(url, country="us")
            if result:
                return result
        except Exception as e:
            logger.warning(f"Standard zone failed for {url}: {e}")

        # Tier 3: Mobile UA
        try:
            result = await self._web_unlocker_rest_api(url, country="us", mobile=True)
            if result:
                logger.info(f"Mobile UA success for {url}")
                return result
        except Exception as e:
            logger.debug(f"Mobile UA failed: {e}")

        # Tier 4: Scraping Browser (strongest — full browser with fingerprinting)
        browser_ws = settings.brightdata_browser_ws
        if browser_ws:
            try:
                content = await self._scraping_browser_fetch(url, browser_ws)
                if content:
                    logger.info(f"Scraping Browser success for {url}")
                    return content
            except Exception as e:
                logger.warning(f"Scraping Browser failed for {url}: {e}")

        # Tier 5: CLI fallback
        logger.info(f"Falling back to CLI for {url}")
        try:
            output = await self._run_cli("scrape", url, "--country", "us", "--timing", timeout=90)
            if output:
                return output
        except BrightDataClientError as e:
            logger.warning(f"CLI failed for {url}: {e}")

        logger.warning(f"All Web Unlocker tiers exhausted for {url}")
        return ""

    async def _web_unlocker_rest_api(
        self, url: str, country: Optional[str] = None, mobile: bool = False, zone: Optional[str] = None
    ) -> str:
        """Fetch URL via Bright Data Web Unlocker REST API directly.

        POST https://api.brightdata.com/request
        Returns the page body content (HTML).

        For Premium Domains (high-difficulty sites like nytimes.com):
        Create a zone with Premium Domains enabled in the Bright Data
        Control Panel, then set BRIGHTDATA_PREMIUM_ZONE to that zone name.
        """
        zone = zone or settings.brightdata_zone or "cli_unlocker"
        payload = {
            "zone": zone,
            "url": url,
            "format": "json",
            "country": country or "us",
        }
        if mobile:
            payload["mobile"] = True

        headers = {
            "Authorization": f"Bearer {settings.brightdata_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.brightdata.com/request",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            body = data.get("body", "")
            status_code = data.get("status_code", 0)
            logger.info(
                f"Web Unlocker REST API: {url} → HTTP {status_code}, "
                f"{len(body)} bytes"
            )
            return body

    async def web_unlocker_post(
        self, url: str, form_data: Dict[str, str], country: Optional[str] = None
    ) -> str:
        """Submit form data to a page via Bright Data Web Unlocker (POST).

        Uses the Web Unlocker REST API with form fields forwarded as part of
        the request body. Falls back to CLI subprocess if the REST API fails.

        Args:
            url: Target URL to POST to.
            form_data: Key-value pairs to submit as the POST body.
            country: 2-letter country code for geo-targeting (e.g., 'us', 'gb').

        Returns:
            Page content (HTML) returned by the server after processing the POST.
        """
        logger.info(f"Web Unlocker POST: {url} ({len(form_data)} fields)")

        # Try REST API first
        try:
            payload = {
                "zone": settings.brightdata_zone or "cli_unlocker",
                "url": url,
                "format": "json",
                "method": "POST",
                "json_data": form_data,
            }
            if country:
                payload["country"] = country

            headers = {
                "Authorization": f"Bearer {settings.brightdata_api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.brightdata.com/request",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                body = data.get("body", "")
                status_code = data.get("status_code", 0)
                logger.info(
                    f"Web Unlocker POST (REST API): {url} -> HTTP {status_code}, "
                    f"{len(body)} bytes"
                )
                return body

        except Exception as e:
            logger.debug(f"Web Unlocker POST REST API failed, trying CLI: {e}")

        # Fallback to CLI subprocess (limited — bdata scrape is GET-oriented)
        args = ["scrape", url, "--method", "POST", "--data", json.dumps(form_data)]
        if country:
            args.extend(["--country", country])
        try:
            output = await self._run_cli(*args, timeout=90)
            return output
        except BrightDataClientError as e:
            logger.warning(f"Web Unlocker POST failed for {url}: {e}")
            return ""

    # ------------------------------------------------------------------ #
    # SERP API
    # ------------------------------------------------------------------ #

    async def _parse_search_output(
        self, output: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Parse the bdata search output which is NDJSON (json lines).

        Normalizes the Bright Data response structure into a clean list
        of result dicts with standard keys: title, url, snippet, source.
        """
        results = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Organic search results
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("description", ""),
                    "source": item.get("source", ""),
                })

            # News search results
            for item in data.get("news", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                })

            if len(results) >= max_results:
                break

        return results[:max_results]

    async def serp_search(
        self,
        query: str,
        source: str = "google",
        country: str = "US",
        language: str = "en",
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform a search and return structured results.

        Args:
            query: Search query string.
            source: Search engine (google, bing, yandex).
            country: 2-letter country code.
            language: Language code (e.g., 'en', 'fr').
            max_results: Maximum results to return.

        Returns:
            List of structured result dicts with title, url, snippet, source.
        """
        logger.info(f"SERP search: '{query}' on {source}")
        args = ["search", query, "--engine", source]
        if country:
            args.extend(["--country", country.lower()])
        if language:
            args.extend(["--language", language])

        try:
            output = await self._run_cli(*args, timeout=60)
            return await self._parse_search_output(output, max_results)
        except BrightDataClientError as e:
            logger.warning(f"SERP search failed for '{query}': {e}")
            return []

    async def serp_news(
        self, query: str, country: str = "US", freshness: str = "7d"
    ) -> List[Dict[str, Any]]:
        """Search for news results.

        Args:
            query: Search query string.
            country: 2-letter country code.
            freshness: Time range (e.g., '7d', '24h', '1h').

        Returns:
            List of structured result dicts with title, url, snippet, source.
        """
        logger.info(f"SERP news search: '{query}'")
        args = [
            "search", query, "--engine", "google",
            "--type", "news",
        ]
        if country:
            args.extend(["--country", country.lower()])
        try:
            output = await self._run_cli(*args, timeout=60)
            return await self._parse_search_output(output, max_results=20)
        except BrightDataClientError as e:
            logger.warning(f"SERP news search failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Scraping Browser — Premium fallback via WebSocket
    # ------------------------------------------------------------------ #

    async def _scraping_browser_fetch(self, url: str, ws_endpoint: str) -> str:
        """Fetch page content via Bright Data Scraping Browser WebSocket.

        This is the strongest anti-detection tier — uses a real headless
        browser with fingerprinting, CAPTCHA solving, and JS rendering.
        Slower and more expensive than Web Unlocker, but succeeds on sites
        that block automated HTTP requests.

        Args:
            url: Target URL to navigate to.
            ws_endpoint: WebSocket endpoint (wss://...).

        Returns:
            Page HTML content as string, or empty string on failure.
        """
        try:
            import asyncio
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(ws_endpoint)
                page = await browser.new_page()
                page.set_default_navigation_timeout(60000)
                await page.goto(url, wait_until="domcontentloaded")
                content = await page.content()
                await browser.close()
                logger.info(f"Scraping Browser fetched {url} ({len(content)} bytes)")
                return content
        except ImportError:
            logger.warning("playwright not installed — cannot use Scraping Browser fallback")
            return ""
        except Exception as e:
            logger.warning(f"Scraping Browser failed for {url}: {e}")
            return ""

    async def scraping_browser_navigate(
        self, url: str, country: Optional[str] = None
    ) -> str:
        """Open a page in a headless browser and return snapshot.

        Args:
            url: Target URL.
            country: Optional 2-letter country code for geo-targeting.

        Returns:
            Browser accessibility tree snapshot as text.
        """
        logger.info(f"Scraping Browser navigating: {url}")
        args = ["browser", "open", url]
        if country:
            args.extend(["--country", country])
        try:
            output = await self._run_cli(*args, timeout=120)
            return output
        except BrightDataClientError as e:
            logger.warning(f"Scraping Browser failed for {url}: {e}")
            return ""

    # ------------------------------------------------------------------ #
    # MCP Server Config
    # ------------------------------------------------------------------ #

    def get_mcp_server_config(self) -> Dict[str, str]:
        """Return MCP Server configuration for AI agent frameworks."""
        return {
            "api_key": self.api_key,
            "username": self.username,
        }


# Singleton
brightdata = BrightDataClient()
