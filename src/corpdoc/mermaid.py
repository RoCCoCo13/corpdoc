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
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

from corpdoc._util import as_bool, warn

# Seconds allowed per diagram before mmdc is killed.
DEFAULT_TIMEOUT = 30

# Diagrams rendered at the same time. Each one starts a headless browser.
MAX_WORKERS = 4

# mmdc renders the bitmap at this device scale so it stays sharp in print;
# the image is then placed at 1 / PNG_SCALE of its pixel size.
PNG_SCALE = 2


class MermaidRenderer:
    """
    Renders Mermaid sources to PNG files for the duration of one render.

    The PNGs must outlive the PDF build (ReportLab reads images lazily),
    so they live in one temp directory that `cleanup()` removes afterwards.
    """

    def __init__(self, cfg=None):
        mcfg = (cfg or {}).get("mermaid")
        if isinstance(mcfg, dict):
            self.enabled = as_bool(mcfg.get("enabled", True), True)
        else:
            # Shorthand: `mermaid: false` switches the feature off.
            self.enabled = True if mcfg is None else as_bool(mcfg, True)
            mcfg = {}
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
        return self.render_all([source])[0]

    def render_all(self, sources):
        """
        Render every diagram of a document. Returns one entry per source,
        in the same order: the path of a PNG, or None for the text fallback.

        Up to MAX_WORKERS diagrams are rendered at the same time. When mmdc
        times out or cannot be started (a problem with the tool, not with one
        diagram), the diagrams not yet started are skipped, so a broken
        installation costs one timeout and not one per diagram.
        """
        sources = list(sources)
        if not sources or not self.enabled:
            return [None] * len(sources)

        mmdc = shutil.which("mmdc")
        if not mmdc:
            if not self._warned_missing:
                self._warned_missing = True
                warn(
                    "Mermaid diagrams are shown as text: the 'mmdc' executable was not "
                    "found on PATH (install with: npm install -g @mermaid-js/mermaid-cli)."
                )
            return [None] * len(sources)

        if self._tmp is None:
            self._tmp = tempfile.mkdtemp(prefix="corpdoc-mermaid-")
        first = self._count + 1
        self._count += len(sources)
        tool_broken = threading.Event()

        def job(number, source):
            if tool_broken.is_set():
                return None, None  # skipped
            path, problem, fatal = self._run(mmdc, number, source)
            if fatal:
                tool_broken.set()
            return path, problem

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(sources))) as pool:
            outcomes = list(pool.map(job, range(first, first + len(sources)), sources))

        # Warnings are printed here, in document order, not from the workers.
        skipped = 0
        for number, (path, problem) in enumerate(outcomes, first):
            if problem:
                warn(f"Mermaid diagram {number}: {problem}; shown as text.")
            elif path is None:
                skipped += 1
        if skipped:
            warn(
                f"{skipped} more Mermaid diagram(s) were not attempted after that problem "
                "with mmdc; shown as text."
            )
        return [path for path, _ in outcomes]

    def _run(self, mmdc, number, source):
        """Run mmdc for one diagram. Returns (png_path or None, problem or None, fatal)."""
        src = os.path.join(self._tmp, f"diagram-{number}.mmd")
        out = os.path.join(self._tmp, f"diagram-{number}.png")
        with open(src, "w", encoding="utf-8") as f:
            f.write(source)

        cmd = [mmdc, "-i", src, "-o", out, "-b", "transparent", "-s", str(PNG_SCALE), "-q"]
        if self.puppeteer_config:
            cmd += ["-p", str(self.puppeteer_config)]

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
            return None, f"mmdc timed out after {self.timeout:g} s", True
        except OSError as exc:
            return None, f"mmdc could not be started ({exc})", True

        if proc.returncode != 0 or not os.path.isfile(out) or os.path.getsize(out) == 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            reason = detail[0][:200] if detail else f"exit code {proc.returncode}, no output file"
            return None, f"mmdc failed ({reason})", False
        return out, None, False

    def cleanup(self):
        """Remove the temp directory with every rendered diagram."""
        if self._tmp is not None:
            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None
