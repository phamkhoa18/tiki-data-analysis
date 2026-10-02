#!/usr/bin/env python3
"""
Enhanced Rate Limiter with Exponential Backoff, Retry Logic, and Rotating User-Agents.
Ensures polite crawling of Tiki APIs while handling rate limits and transient errors.
"""

import time
import random
import logging
from functools import wraps

try:
    from .config import (
        API_DELAY_MIN, API_DELAY_MAX, MAX_RETRIES,
        RETRY_BACKOFF_BASE, USER_AGENTS, REQUEST_TIMEOUT
    )
except ImportError:
    from config import (
        API_DELAY_MIN, API_DELAY_MAX, MAX_RETRIES,
        RETRY_BACKOFF_BASE, USER_AGENTS, REQUEST_TIMEOUT
    )

logger = logging.getLogger("TikiRateLimiter")


class PoliteRateLimiter:
    """
    Polite rate limiter with:
    - Configurable random delay between requests
    - Exponential backoff on rate limit (HTTP 429) or server errors (5xx)
    - Auto-retry with max attempts
    - Rotating User-Agent headers
    - Jitter to prevent thundering herd
    """

    def __init__(self, min_delay=None, max_delay=None, max_retries=None):
        self.min_delay = min_delay or API_DELAY_MIN
        self.max_delay = max_delay or API_DELAY_MAX
        self.max_retries = max_retries or MAX_RETRIES
        self.last_request_time = 0
        self.total_requests = 0
        self.total_retries = 0
        self.total_errors = 0

    def wait(self):
        """Wait a random delay between min_delay and max_delay before next request."""
        elapsed = time.time() - self.last_request_time
        sleep_target = random.uniform(self.min_delay, self.max_delay)
        if elapsed < sleep_target:
            time.sleep(sleep_target - elapsed)
        self.last_request_time = time.time()
        self.total_requests += 1

    def backoff_wait(self, attempt):
        """
        Exponential backoff with jitter.
        attempt 1 → ~2s, attempt 2 → ~4s, attempt 3 → ~8s
        """
        base_wait = RETRY_BACKOFF_BASE ** attempt
        jitter = random.uniform(0, base_wait * 0.3)  # 30% jitter
        total_wait = base_wait + jitter
        logger.warning(f"Backoff: waiting {total_wait:.1f}s (attempt {attempt}/{self.max_retries})")
        time.sleep(total_wait)
        self.total_retries += 1

    def get_headers(self):
        """Get HTTP headers that match the Safari 17 impersonation profile."""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://tiki.vn/",
        }

    def get_scrape_headers(self):
        """Get HTTP headers for web scraping (HTML pages)."""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://tiki.vn/",
        }

    def request_with_retry(self, session, method, url, **kwargs):
        """
        Make an HTTP request with automatic retry, exponential backoff,
        and automatic Byte-nginx WAF challenge solving.
        
        Returns:
            requests.Response on success, None on failure after all retries.
        """
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs.setdefault("headers", self.get_headers())

        for attempt in range(1, self.max_retries + 1):
            self.wait()
            try:
                resp = session.request(method, url, **kwargs)

                if resp.status_code == 200:
                    # Check for Tiki Byte-nginx JavaScript anti-bot challenge
                    text_head = resp.text[:300] if resp.text else ""
                    if "<!DOCTYPE html>" in text_head and ("_0x" in resp.text or "challenge" in resp.text.lower()):
                        logger.warning(f"  🛡️ Tiki WAF challenge detected on {url}. Auto-solving with Node sandbox...")
                        try:
                            from .waf_solver import solve_waf_challenge
                        except ImportError:
                            from waf_solver import solve_waf_challenge

                        cookie_dict = solve_waf_challenge(resp.text, url)
                        if cookie_dict:
                            for ck, cv in cookie_dict.items():
                                session.cookies.set(ck, cv)
                            time.sleep(1.0)
                            continue  # Retry request with solved cookie
                        else:
                            self.backoff_wait(attempt)
                            continue

                    return resp

                if resp.status_code == 429:
                    logger.warning(f"Rate limited (429) on {url}")
                    if attempt < self.max_retries:
                        self.backoff_wait(attempt)
                        continue
                    else:
                        logger.error(f"Rate limited after {self.max_retries} retries: {url}")
                        self.total_errors += 1
                        return None

                if resp.status_code >= 500:
                    logger.warning(f"Server error ({resp.status_code}) on {url}")
                    if attempt < self.max_retries:
                        self.backoff_wait(attempt)
                        continue
                    else:
                        logger.error(f"Server error after {self.max_retries} retries: {url}")
                        self.total_errors += 1
                        return None

                # Client error (4xx, not 429) — don't retry
                logger.warning(f"Client error ({resp.status_code}) on {url} — skipping")
                self.total_errors += 1
                return None

            except Exception as e:
                logger.warning(f"Request error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    self.backoff_wait(attempt)
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {url} — {e}")
                    self.total_errors += 1
                    return None

        return None

    def get_stats(self):
        """Return crawling statistics."""
        return {
            "total_requests": self.total_requests,
            "total_retries": self.total_retries,
            "total_errors": self.total_errors,
        }

    def __repr__(self):
        return (
            f"PoliteRateLimiter(delay={self.min_delay}-{self.max_delay}s, "
            f"retries={self.max_retries}, requests={self.total_requests})"
        )
