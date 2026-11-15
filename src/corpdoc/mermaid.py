"""
Local Mermaid rendering.

Diagrams are rendered with the Mermaid CLI (`mmdc`, from the npm package
`@mermaid-js/mermaid-cli`) when it is on PATH. Everything happens on this
machine: the diagram source is written to a private temp directory, `mmdc`
turns it into a PNG there, and the PNG is embedded like any other image.
Diagram content is never sent to an external service.

When `mmdc` is missing, fails or times out, the caller keeps the text
fallback and a warning is printed.
"""

import os
import shutil
import subprocess
import sys
import tempfile

# Seconds allowed per diagram before mmdc is killed.
DEFAULT_TIMEOUT = 30

# mmdc renders the bitmap at this device scale so it stays sharp in print;
# the image is then placed at 1 / PNG_SCALE of its pixel size.
PNG_SCALE = 2


def _warn(message):
    print(f"Warning: {message}", file=sys.stderr)


class MermaidRenderer:
    """
    Renders Mermaid sources to PNG files for the duration of one render.

    The PNGs must outlive the PDF build (ReportLab reads images lazily),
    so they live in one temp directory that `cleanup()` removes afterwards.
    """

    def __init__(self, cfg=None):
        mcfg = (cfg or {}).get("mermaid") or {}
        self.enabled = mcfg.get("enabled", True) is not False
        self.puppeteer_config = mcfg.get("puppeteer_config") or ""
        try:
            self.timeout = float(mcfg.get("timeout", DEFAULT_TIMEOUT))
        except (TypeError, ValueError):
            self.timeout = DEFAULT_TIMEOUT
        if self.timeout <= 0:
            self.timeout = DEFAULT_TIMEOUT
        self._tmp = None
        self._count = 0
        self._warned_missing = False

    def render(self, source):
        """Return the path of a PNG for `source`, or None to use the text fallback."""
        if not self.enabled:
            return None

        mmdc = shutil.which("mmdc")
        if not mmdc:
            if not self._warned_missing:
                self._warned_missing = True
                _warn(
                    "Mermaid diagrams are shown as text: the 'mmdc' executable was not "
                    "found on PATH (install with: npm install -g @mermaid-js/mermaid-cli)."
                )
            return None

        if self._tmp is None:
            self._tmp = tempfile.mkdtemp(prefix="corpdoc-mermaid-")
        self._count += 1
        src = os.path.join(self._tmp, f"diagram-{self._count}.mmd")
        out = os.path.join(self._tmp, f"diagram-{self._count}.png")
        with open(src, "w", encoding="utf-8") as f:
            f.write(source)

        cmd = [mmdc, "-i", src, "-o", out, "-b", "transparent", "-s", str(PNG_SCALE), "-q"]
        if self.puppeteer_config:
            cmd += ["-p", str(self.puppeteer_config)]

        label = f"Mermaid diagram {self._count}"
        try:
            proc = subprocess.run(  # fixed argv, never through a shell
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            _warn(f"{label}: mmdc timed out after {self.timeout:g} s; shown as text.")
            return None
        except OSError as exc:
            _warn(f"{label}: mmdc could not be started ({exc}); shown as text.")
            return None

        if proc.returncode != 0 or not os.path.isfile(out) or os.path.getsize(out) == 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            reason = detail[0][:200] if detail else f"exit code {proc.returncode}, no output file"
            _warn(f"{label}: mmdc failed ({reason}); shown as text.")
            return None
        return out

    def cleanup(self):
        """Remove the temp directory with every rendered diagram."""
        if self._tmp is not None:
            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None
