"""Resolve changed bundle files to skill roots without executing bundle content."""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path


def roots_for_changes(root, changed):
    root=root.resolve();found=set()
    for name in changed:
        path=(root/name).resolve()
        if not path.is_relative_to(root):raise ValueError("changed_path_outside_repository")
        if "examples/skill-trust-gate/test-fixtures/" in path.relative_to(root).as_posix():continue
        if path.name.endswith(".skill.md"):
            found.add(path.parent.relative_to(root).as_posix());continue
        for parent in [path.parent,*path.parent.parents]:
            if not parent.is_relative_to(root):break
            if (parent/"SKILL.md").is_file() and any(entry.name=="SKILL.md" for entry in parent.iterdir()):
                found.add(parent.relative_to(root).as_posix());break
    return sorted(found)


def main():
    root=Path.cwd();event=os.environ.get("EVENT_NAME","")
    if event=="workflow_dispatch":
        target=Path(os.environ["DISPATCH_SKILL_PATH"])
        if target.is_absolute():raise ValueError("dispatch_path_must_be_relative")
        paths=roots_for_changes(root,[str(target/"SKILL.md")])
        if not paths:raise ValueError("dispatch_skill_not_found")
    else:
        before=os.environ.get("BEFORE_SHA","")
        base=os.environ.get("BASE_REF","")
        if event=="push" and before and set(before)!={"0"}:args=[before,"HEAD"]
        elif base:args=["origin/"+base+"...HEAD"]
        else:args=["HEAD~1","HEAD"]
        changed=subprocess.run(["git","diff","--name-only",*args],capture_output=True,text=True,check=True).stdout.splitlines()
        paths=roots_for_changes(root,changed)
    with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as output:
        output.write("has_skills="+("true" if paths else "false")+"\n")
        output.write("paths="+json.dumps(paths)+"\n")


if __name__=="__main__":main()
