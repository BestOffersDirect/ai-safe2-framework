"""Fail closed on incomplete skill discovery or scan execution."""
import os


def decision(discovery, has_skills, scan):
    if discovery!="success":raise ValueError("skill_discovery_incomplete")
    if has_skills=="false":
        if scan!="skipped":raise ValueError("unexpected_scan_state_for_no_changed_skills")
        return "not-applicable: no changed skill bundles"
    if has_skills!="true":raise ValueError("skill_applicability_unknown")
    if scan!="success":raise ValueError("required_skill_scan_not_successful")
    return "pass: all changed skill bundles scanned successfully"


def main():
    try:print(decision(os.environ.get("DISCOVERY_RESULT"),os.environ.get("HAS_SKILLS"),os.environ.get("SCAN_RESULT")))
    except ValueError as exc:
        print(str(exc));return 1
    return 0


if __name__=="__main__":raise SystemExit(main())
