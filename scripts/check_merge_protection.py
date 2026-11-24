"""Audit the declared and live merge protections without modifying repository settings."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def policy_errors(policy):
    errors=[]
    checks=policy.get("required_status_checks",[])
    names=[c.get("context") for c in checks]
    if not checks or len(names)!=len(set(names)) or any(not n for n in names):
        errors.append("missing_or_duplicate_required_checks")
    if any(not isinstance(c.get("integration_id"),int) or c["integration_id"]<=0 for c in checks):
        errors.append("required_check_emitter_not_pinned")
    if set(names)&set(policy.get("advisory_contexts",[])):
        errors.append("advisory_provider_made_mandatory")
    for key in ["strict_required_status_checks_policy","required_review_thread_resolution","dismiss_stale_reviews_on_push"]:
        if policy.get(key) is not True:
            errors.append(key+"_disabled")
    if policy.get("bypass_actors")!=[]:
        errors.append("merge_bypass_present")
    return errors


def compare_ruleset(policy, actual):
    errors=policy_errors(policy)
    if actual.get("enforcement")!="active" or actual.get("target")!="branch":
        errors.append("ruleset_not_active_for_branches")
    refs=actual.get("conditions",{}).get("ref_name",{})
    if not {"~DEFAULT_BRANCH","refs/heads/"+policy["branch"]}&set(refs.get("include",[])) or refs.get("exclude"):
        errors.append("default_branch_not_fully_covered")
    if actual.get("bypass_actors",[])!=[]:
        errors.append("live_merge_bypass_present")
    rules={r["type"]:r.get("parameters",{}) for r in actual.get("rules",[])}
    for kind in ["deletion","non_fast_forward","pull_request","required_status_checks"]:
        if kind not in rules:errors.append("missing_rule:"+kind)
    status=rules.get("required_status_checks",{})
    active={(c["context"],c.get("integration_id")) for c in status.get("required_status_checks",[])}
    for c in policy["required_status_checks"]:
        if (c["context"],c["integration_id"]) not in active:
            errors.append("missing_or_wrong_emitter:"+c["context"])
    if status.get("strict_required_status_checks_policy") is not True or status.get("do_not_enforce_on_create",False):
        errors.append("fresh_head_checks_not_enforced")
    if any(name in policy.get("advisory_contexts",[]) for name,_ in active):
        errors.append("live_advisory_provider_made_mandatory")
    pr=rules.get("pull_request",{})
    for key in ["required_review_thread_resolution","dismiss_stale_reviews_on_push"]:
        if pr.get(key) is not True:errors.append("live_"+key+"_disabled")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--snapshot",type=Path)
    args=parser.parse_args()
    policy=json.loads((ROOT/".github/required-checks.json").read_text(encoding="utf-8"))
    errors=policy_errors(policy)
    if args.live and args.snapshot:parser.error("choose --live or --snapshot")
    if args.live:
        repo=subprocess.run(["gh","api",f"repos/{policy['repository']}"],capture_output=True,text=True)
        if repo.returncode or json.loads(repo.stdout).get("default_branch")!=policy["branch"]:
            print("Default branch identity unavailable or disagrees with policy.");return 1
        route=f"repos/{policy['repository']}/rulesets/{policy['ruleset_id']}"
        result=subprocess.run(["gh","api",route],capture_output=True,text=True)
        if result.returncode:
            print("Live protection audit unavailable; no enforcement pass is claimed.")
            return 1
        errors=compare_ruleset(policy,json.loads(result.stdout))
    elif args.snapshot:
        errors=compare_ruleset(policy,json.loads(args.snapshot.read_text(encoding="utf-8-sig")))
    for error in errors:print(error)
    if not errors:print("Merge protection "+("live rules" if args.live or args.snapshot else "contract")+" passed")
    return bool(errors)


if __name__=="__main__":raise SystemExit(main())
