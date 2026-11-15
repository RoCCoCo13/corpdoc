"""One CorpDoc object can render several documents at the same time."""

import threading

import pytest
from PIL import Image as PILImage
from test_render import MINIMAL_CONFIG

from corpdoc import api
from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

MD = "# T\n\n![Figure](a.png)\n"


def test_two_renders_at_once_keep_their_own_base_dir(tmp_path, monkeypatch):
    with_image = tmp_path / "with"
    without_image = tmp_path / "without"
    with_image.mkdir()
    without_image.mkdir()
    PILImage.new("RGB", (60, 30), (200, 30, 30)).save(with_image / "a.png")
    (with_image / "doc.md").write_text(MD, encoding="utf-8")
    (without_image / "doc.md").write_text(MD, encoding="utf-8")

    # Hold both renders at the same point (after each has read its input),
    # so they overlap for certain.
    barrier = threading.Barrier(2, timeout=10)
    real_parse = api.parse_blocks

    def parse_when_both_started(*args, **kwargs):
        barrier.wait()
        return real_parse(*args, **kwargs)

    monkeypatch.setattr(api, "parse_blocks", parse_when_both_started)

    doc = CorpDoc(config=MINIMAL_CONFIG)
    results, errors = {}, []

    def run(folder):
        try:
            results[folder.name] = doc.render(str(folder / "doc.md"), output=str(folder / "o.pdf"))
        except Exception as exc:  # noqa: BLE001 - reported by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=run, args=(d,)) for d in (with_image, without_image)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)

    assert not errors

    def images(folder):
        return sum(len(p.images) for p in pypdf.PdfReader(folder / "o.pdf").pages)

    assert images(with_image) == 1
    assert images(without_image) == 0
    assert results["with"].total_pages == results["without"].total_pages == 4


def test_render_leaves_no_per_document_state_on_the_object(tmp_path):
    doc = CorpDoc(config=MINIMAL_CONFIG)
    before = set(vars(doc))
    doc.render("# T\n\nBody.\n", output=str(tmp_path / "o.pdf"), base_dir=str(tmp_path))
    # Only the documented page counts may change.
    assert set(vars(doc)) - before <= {"total_pages", "body_pages"}
    assert not hasattr(doc, "_base_dir") and not hasattr(doc, "_mermaid")
