"""Tests for local Mermaid rendering through the `mmdc` executable.

`mmdc` is not required to run these tests: the subprocess is replaced by a
fake that behaves like the CLI (writes a PNG to the path after `-o`).
"""

import os
import subprocess

import pytest
from PIL import Image as PILImage
from test_render import MINIMAL_CONFIG

from corpdoc import mermaid
from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

MD = "# Flow\n\n```mermaid\nflowchart LR\n    Alpha --> Beta\n```\n\nAfter the diagram.\n"
BODY_ONLY = {"sections": {"cover": False, "version_history": False, "toc": False}}


class FakeMmdc:
    """Stands in for subprocess.run when the command is mmdc."""

    def __init__(self, mode="ok"):
        self.mode = mode
        self.calls = []
        self.work_dirs = []
        self.sources = []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        src, out = cmd[cmd.index("-i") + 1], cmd[cmd.index("-o") + 1]
        self.work_dirs.append(os.path.dirname(out))
        with open(src, encoding="utf-8") as f:
            self.sources.append(f.read())
        if self.mode == "timeout":
            raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))
        if self.mode == "fail":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Parse error on line 2")
        if self.mode == "no-output":
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        PILImage.new("RGB", (800, 400), (240, 240, 255)).save(out)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


@pytest.fixture
def fake_mmdc(monkeypatch):
    def install(mode="ok", available=True):
        fake = FakeMmdc(mode)
        monkeypatch.setattr(
            mermaid.shutil, "which", lambda name: "/fake/bin/mmdc" if available else None
        )
        monkeypatch.setattr(mermaid.subprocess, "run", fake)
        return fake

    return install


def _render(tmp_path, md=MD, **cfg):
    out = tmp_path / "out.pdf"
    CorpDoc(config={**MINIMAL_CONFIG, **BODY_ONLY, **cfg}).render(md, output=str(out))
    reader = pypdf.PdfReader(out)
    text = "\n".join(p.extract_text() for p in reader.pages)
    return text, sum(len(p.images) for p in reader.pages)


def test_without_mmdc_keeps_text_fallback_and_warns(tmp_path, fake_mmdc, capsys):
    fake = fake_mmdc(available=False)
    text, images = _render(tmp_path)

    assert images == 0
    assert "[ Diagram ]" in text and "Alpha --> Beta" in text
    err = capsys.readouterr().err
    assert "Warning" in err and "mmdc" in err
    assert fake.calls == []


def test_missing_mmdc_warns_once_for_many_diagrams(tmp_path, fake_mmdc, capsys):
    fake_mmdc(available=False)
    _render(tmp_path, md=MD + "\n" + MD.replace("# Flow", "# Again"))
    assert capsys.readouterr().err.count("mmdc") == 1


def test_with_mmdc_embeds_the_diagram_as_an_image(tmp_path, fake_mmdc, capsys):
    fake = fake_mmdc()
    text, images = _render(tmp_path)

    assert images == 1
    assert "[ Diagram ]" not in text and "Alpha --> Beta" not in text
    assert "After the diagram." in text
    assert capsys.readouterr().err == ""

    assert len(fake.calls) == 1
    cmd, kwargs = fake.calls[0]
    assert cmd[0] == "/fake/bin/mmdc"
    assert cmd[cmd.index("-o") + 1].endswith(".png")
    assert kwargs.get("shell") is not True
    assert "flowchart LR" in fake.sources[0]


def test_mmdc_runs_with_a_timeout(tmp_path, fake_mmdc):
    fake = fake_mmdc()
    _render(tmp_path)
    assert fake.calls[0][1]["timeout"] == mermaid.DEFAULT_TIMEOUT

    fake = fake_mmdc()
    _render(tmp_path, mermaid={"timeout": 5})
    assert fake.calls[0][1]["timeout"] == 5


@pytest.mark.parametrize("mode", ["timeout", "fail", "no-output"])
def test_mmdc_problem_falls_back_to_text_with_warning(tmp_path, fake_mmdc, capsys, mode):
    fake_mmdc(mode)
    text, images = _render(tmp_path)

    assert images == 0
    assert "[ Diagram ]" in text and "Alpha --> Beta" in text
    err = capsys.readouterr().err
    assert "Warning" in err and "Mermaid" in err


@pytest.mark.parametrize("mode", ["ok", "timeout", "fail"])
def test_temp_files_are_cleaned_up(tmp_path, fake_mmdc, mode):
    fake = fake_mmdc(mode)
    _render(tmp_path)
    assert fake.work_dirs
    assert not any(os.path.exists(d) for d in fake.work_dirs)


def test_temp_files_are_cleaned_up_when_the_build_fails(tmp_path, fake_mmdc, monkeypatch):
    fake = fake_mmdc()
    doc = CorpDoc(config={**MINIMAL_CONFIG, **BODY_ONLY})

    def boom(*args, **kwargs):
        raise RuntimeError("build failed")

    monkeypatch.setattr("corpdoc.api.CorpDocTemplate.build", boom)
    with pytest.raises(RuntimeError):
        doc.render(MD, output=str(tmp_path / "out.pdf"))
    assert fake.work_dirs and not os.path.exists(fake.work_dirs[0])


def test_mermaid_can_be_disabled(tmp_path, fake_mmdc, capsys):
    fake = fake_mmdc()
    text, images = _render(tmp_path, mermaid={"enabled": False})
    assert images == 0 and "[ Diagram ]" in text
    assert fake.calls == []
    assert capsys.readouterr().err == ""


def test_no_network_code_in_the_package():
    """Diagram source must never leave the machine: no HTTP client, no Kroki."""
    import pathlib

    import corpdoc

    for path in pathlib.Path(corpdoc.__file__).parent.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for needle in ("kroki", "import requests", "urllib.request", "http.client", "urlopen"):
            assert needle not in source, f"{needle!r} found in {path.name}"

    pyproject = (pathlib.Path(__file__).parent.parent / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "requests" not in pyproject


@pytest.mark.parametrize(
    "setting", [False, {"enabled": "false"}, {"enabled": "no"}, {"enabled": 0}, {"enabled": "off"}]
)
def test_mermaid_disabled_accepts_false_like_values(tmp_path, fake_mmdc, capsys, setting):
    fake = fake_mmdc()
    text, images = _render(tmp_path, mermaid=setting)
    assert images == 0 and "[ Diagram ]" in text
    assert fake.calls == []
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("setting", [True, {"enabled": "yes"}, {"enabled": "typo"}, {}, None])
def test_mermaid_stays_enabled_for_true_like_or_unknown_values(tmp_path, fake_mmdc, setting):
    fake = fake_mmdc()
    _, images = _render(tmp_path, mermaid=setting)
    assert images == 1 and len(fake.calls) == 1


# ── Several diagrams ──────────────────────────────────────────────────────


class SlowMmdc(FakeMmdc):
    """Takes a moment per diagram and records how many run at the same time."""

    def __init__(self, mode="ok"):
        super().__init__(mode)
        self._lock = __import__("threading").Lock()
        self.active = 0
        self.max_active = 0

    def __call__(self, cmd, **kwargs):
        import time

        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.05)
            src, out = cmd[cmd.index("-i") + 1], cmd[cmd.index("-o") + 1]
            with open(src, encoding="utf-8") as f:
                source = f.read()
            with self._lock:
                self.calls.append((cmd, kwargs))
                self.sources.append(source)
            if self.mode == "timeout":
                raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))
            # The picture width identifies the diagram: "N3" -> 300 px wide.
            number = int(source.split("N")[1].split()[0])
            PILImage.new("RGB", (number * 100, 50), (240, 240, 255)).save(out)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        finally:
            with self._lock:
                self.active -= 1


def _many(n):
    return "# Flow\n\n" + "".join(
        f"Text {i}.\n\n```mermaid\nflowchart LR\n    N{i} --> End\n```\n\n" for i in range(1, n + 1)
    )


def _install(monkeypatch, fake):
    lookups = []

    def which(name):
        lookups.append(name)
        return "/fake/bin/mmdc"

    monkeypatch.setattr(mermaid.shutil, "which", which)
    monkeypatch.setattr(mermaid.subprocess, "run", fake)
    return lookups


def test_diagrams_render_in_parallel_and_stay_in_document_order(tmp_path, monkeypatch):
    fake = SlowMmdc()
    lookups = _install(monkeypatch, fake)
    out = tmp_path / "out.pdf"

    CorpDoc(config={**MINIMAL_CONFIG, **BODY_ONLY}).render(_many(6), output=str(out))

    assert len(fake.calls) == 6
    assert fake.max_active > 1  # not one after another
    assert fake.max_active <= mermaid.MAX_WORKERS
    widths = [im.image.size[0] for p in pypdf.PdfReader(out).pages for im in p.images]
    assert sorted(widths) == [100, 200, 300, 400, 500, 600]
    assert lookups == ["mmdc"]  # looked up once per render, not once per diagram


def test_parallel_results_come_back_in_source_order(monkeypatch):
    _install(monkeypatch, SlowMmdc())
    renderer = mermaid.MermaidRenderer({})
    try:
        sources = [f"flowchart LR\n    N{i} --> End\n" for i in (3, 1, 6, 2, 5, 4)]
        paths = renderer.render_all(sources)
        widths = []
        for path in paths:
            with PILImage.open(path) as im:
                widths.append(im.size[0])
        assert widths == [300, 100, 600, 200, 500, 400]
    finally:
        renderer.cleanup()


def test_after_a_timeout_no_further_diagrams_are_started(tmp_path, monkeypatch, capsys):
    fake = SlowMmdc("timeout")
    _install(monkeypatch, fake)
    out = tmp_path / "out.pdf"

    CorpDoc(config={**MINIMAL_CONFIG, **BODY_ONLY}).render(_many(12), output=str(out))

    # Only the diagrams already running when the first one timed out.
    assert 1 <= len(fake.calls) <= mermaid.MAX_WORKERS
    text = "\n".join(p.extract_text() for p in pypdf.PdfReader(out).pages)
    assert text.count("[ Diagram ]") == 12  # every diagram falls back to text
    err = capsys.readouterr().err
    assert "timed out" in err and "not attempted" in err


def test_a_diagram_with_a_syntax_error_does_not_stop_the_others(tmp_path, monkeypatch, capsys):
    class OneBad(SlowMmdc):
        def __call__(self, cmd, **kwargs):
            with open(cmd[cmd.index("-i") + 1], encoding="utf-8") as f:
                if "N2 " in f.read():
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Parse error")
            return super().__call__(cmd, **kwargs)

    fake = OneBad()
    _install(monkeypatch, fake)
    out = tmp_path / "out.pdf"

    CorpDoc(config={**MINIMAL_CONFIG, **BODY_ONLY}).render(_many(5), output=str(out))

    widths = [im.image.size[0] for p in pypdf.PdfReader(out).pages for im in p.images]
    assert sorted(widths) == [100, 300, 400, 500]
    assert "Mermaid diagram 2" in capsys.readouterr().err


def test_text_fallback_keeps_special_characters(tmp_path, fake_mmdc):
    fake_mmdc(available=False)
    md = "# Flow\n\n```mermaid\nflowchart LR\n    A[R&D <b>team</b>] --> B\n```\n"
    text, _ = _render(tmp_path, md=md)
    assert "A[R&D <b>team</b>] --> B" in " ".join(text.split())
