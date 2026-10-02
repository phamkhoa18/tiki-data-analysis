#!/usr/bin/env python3
"""
Byte-nginx / Tiki WAF Challenge Auto-Solver
Executes the client-side JavaScript challenge inside a lightweight Node.js sandbox
to extract the `_wafchallengeid` verification cookie and bypass anti-bot challenges.
"""

import os
import re
import shutil
import tempfile
import logging
import subprocess

logger = logging.getLogger("WafSolver")

NODE_AVAILABLE = shutil.which("node") is not None


def solve_waf_challenge(html_content: str, url: str = "https://tiki.vn/") -> dict:
    """
    Solve Byte-nginx / Tiki JavaScript WAF challenge.
    
    Args:
        html_content: Raw HTML text containing the obfuscated JS challenge
        url: Request URL
        
    Returns:
        dict with cookies to set on session, or empty dict if solving failed
    """
    if not NODE_AVAILABLE:
        logger.debug("Node.js not found in PATH — cannot solve JS challenge")
        return {}

    match = re.search(r"<script>([\s\S]*?)</script>", html_content)
    if not match:
        return {}

    js_code = match.group(1)

    node_script = f"""
    let solved = null;
    const fakeDoc = {{
      get cookie() {{ return solved || ''; }},
      set cookie(val) {{ solved = val; }}
    }};
    const fakeWin = {{
      location: {{
        reload: () => {{
          if (solved) {{
            process.stdout.write(solved);
          }}
          process.exit(0);
        }},
        href: '{url}'
      }},
      document: fakeDoc
    }};
    global.window = fakeWin;
    global.document = fakeDoc;
    global.location = fakeWin.location;
    global.navigator = {{ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36' }};
    try {{
      {js_code}
    }} catch(e) {{
      process.exit(1);
    }}
    setTimeout(() => {{
      if (solved) {{
        process.stdout.write(solved);
      }}
      process.exit(0);
    }}, 1000);
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(node_script)
        temp_path = f.name

    try:
        res = subprocess.run(
            ["node", temp_path],
            capture_output=True,
            text=True,
            timeout=3,
        )
        raw_cookie = res.stdout.strip()
        if raw_cookie and "=" in raw_cookie:
            first_cookie = raw_cookie.split(";")[0].strip()
            name, val = first_cookie.split("=", 1)
            logger.info(f"  🛡️ Solved Tiki WAF challenge: {name}={val[:20]}...")
            return {name: val}
    except Exception as e:
        logger.warning(f"Failed to execute WAF challenge solver: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {}
