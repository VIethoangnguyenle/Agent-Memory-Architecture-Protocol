import importlib.util
import json
from pathlib import Path


MOD = Path(__file__).resolve().parents[1] / "write_gate.py"
spec = importlib.util.spec_from_file_location("write_gate", MOD)
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)


def test_extracts_file_path_from_claude_write_payload():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "src/App.java"}}
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]


def test_extracts_paths_from_codex_apply_patch_payload():
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n"
            "*** Update File: src/App.java\n"
            "@@\n"
            "-old\n"
            "+new\n"
            "*** Add File: docs/superpowers/specs/x.md\n"
            "+# Spec\n"
            "*** End Patch\n"
        },
    }
    assert wg.extract_target_paths(payload) == [
        Path("src/App.java"),
        Path("docs/superpowers/specs/x.md"),
    ]


def test_extracts_path_from_antigravity_toolcall_payload():
    payload = {
        "toolCall": {
            "name": "replace_file_content",
            "args": {"file_path": "src/App.java"},
        }
    }
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]


def test_allows_framework_and_openspec_artifact_writes(tmp_path):
    assert wg.evaluate_write(tmp_path, Path(".amap/knowledge/active/KNOWLEDGE_CHECKPOINT.md")).ok is True
    assert wg.evaluate_write(tmp_path, Path("openspec/changes/x/specs/foo/spec.md")).ok is True


def test_blocks_app_write_without_checkpoint(tmp_path):
    result = wg.evaluate_write(tmp_path, Path("src/App.java"))
    assert result.ok is False
    assert "KNOWLEDGE_CHECKPOINT" in result.reason


def test_allows_app_write_with_valid_checkpoint(tmp_path):
    framework = tmp_path / ".amap"
    checkpoint = framework / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "## DNA\nSP-6 staircase\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )

    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is True


def test_blocks_app_write_when_checkpoint_ruleid_not_in_index(tmp_path):
    framework = tmp_path / ".amap"
    checkpoint = framework / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "## DNA\nISO-9001\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )
    index = framework / "knowledge" / "long-term" / "knowledge-index.yaml"
    index.parent.mkdir(parents=True)
    index.write_text(
        "entries:\n"
        "  - id: SP-6\n"
        "    store: author-dna\n"
        "    title: staircase\n"
        "    applies_to: [Constructor]\n",
        encoding="utf-8",
    )

    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is False
    assert "valid rule-id" in result.reason


def test_main_blocks_with_exit_2_for_claude_pretooluse(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": "src/App.java"}}
    code = wg.main(["--framework-root", ".claude"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 2
    assert "KNOWLEDGE_CHECKPOINT" in captured.err


def test_main_blocks_when_edit_payload_has_no_target_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"content": "x"}}
    code = wg.main(["--framework-root", ".claude"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 2
    assert "Unable to identify target path" in captured.err


def test_main_blocks_with_codex_json_decision(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n*** Update File: src/App.java\n@@\n-x\n+y\n*** End Patch\n"
        },
    }
    code = wg.main(["--framework-root", ".agents", "--runtime", "codex"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 0
    out = json.loads(captured.out)
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_blocks_with_antigravity_json_decision(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"toolCall": {"name": "write_to_file", "args": {"file_path": "src/App.java"}}}
    code = wg.main(["--framework-root", ".agents", "--runtime", "antigravity"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 0
    assert json.loads(captured.out)["decision"] == "deny"
