import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "NEXUS"
STANDARDS = NEXUS / "standards"


def test_execution_authority_crosswalk_is_complete_and_resolvable() -> None:
    payload = json.loads(
        (STANDARDS / "execution-authority-crosswalk.json").read_text(encoding="utf-8")
    )
    requirements = payload["requirements"]
    assert [item["id"] for item in requirements] == [
        f"ETA-{index}" for index in range(1, 21)
    ]
    assert set(payload["status_vocabulary"]) == {"implemented", "partial", "gap"}
    for item in requirements:
        assert item["status"] in payload["status_vocabulary"]
        assert item["evidence"]
        for relative in item["evidence"]:
            assert (NEXUS / relative).exists(), f"missing ETA evidence: {relative}"
        if item["status"] == "implemented":
            assert item["gap"] is None
        else:
            assert item["gap"]


def test_execution_authority_draft_source_is_well_formed_and_identified() -> None:
    source = (
        STANDARDS
        / "ietf"
        / "draft-sullivan-wimse-execution-authority-00.xml"
    )
    root = ET.parse(source).getroot()
    series = root.find("./front/seriesInfo")
    assert series is not None
    assert series.attrib["value"] == (
        "draft-sullivan-wimse-execution-authority-00"
    )
    text = source.read_text(encoding="utf-8")
    for index in range(1, 21):
        assert f"ETA-{index}" in text


def test_standards_documents_are_discoverable() -> None:
    required = {
        "README.md",
        "EXECUTION-AUTHORITY-CROSSWALK.md",
        "SUBMISSION-PLAN.md",
        "IETF-LIST-REVIEWS.md",
        "STANDARDS-BODY-BRIEFS.md",
        "execution-authority-crosswalk.json",
    }
    assert required <= {path.name for path in STANDARDS.iterdir()}
    manifest = json.loads(
        (NEXUS / "nexus-docs.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["standards"]["entry_point"] == "standards/README.md"

