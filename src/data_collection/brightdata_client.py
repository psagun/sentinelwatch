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

        Uses Bright Data Web Unlocker REST API directly (more reliable than
        CLI subprocess for server environments), with CLI as fallback.

        Args:
            url: Target URL to retrieve.
            country: 2-letter country code for geo-targeting (e.g., 'us', 'gb').
            render: Whether to wait for JS rendering before returning.

        Returns:
            Page content as markdown text.
        """
        logger.info(f"Web Unlocker fetching: {url}")

        # Try direct REST API first (more reliable from server processes)
        try:
            result = await self._web_unlocker_rest_api(url, country)
            if result:
                return result
        except Exception as e:
            logger.debug(f"REST API method failed, trying CLI: {e}")

        # Fallback to CLI subprocess
        args = ["scrape", url]
        if country:
            args.extend(["--country", country])
        try:
            output = await self._run_cli(*args, timeout=90)
            return output
        except BrightDataClientError as e:
            logger.warning(f"Web Unlocker failed for {url}: {e}")
            return ""

    async def _web_unlocker_rest_api(
        self, url: str, country: Optional[str] = None
    ) -> str:
        """Fetch URL via Bright Data Web Unlocker REST API directly.

        POST https://api.brightdata.com/request
        Returns the page body content (HTML).
        """
        payload = {
            "zone": settings.brightdata_zone or "cli_unlocker",
            "url": url,
            "format": "json",
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
    # Scraping Browser
    # ------------------------------------------------------------------ #

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
