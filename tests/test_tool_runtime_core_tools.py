from __future__ import annotations

from tangku_agentos.tool_runtime import ToolManager, ToolRequest, register_builtin_tools


def test_core_tool_runtime_registers_and_executes_file_and_workspace_tools(tmp_path) -> None:
    manager = ToolManager()
    register_builtin_tools(manager, workspace_root=str(tmp_path))

    write_tool = manager.get_tool("file_write")
    write_response = write_tool.execute(
        ToolRequest(
            request_id="req-write",
            tool_id="file_write",
            payload={"path": "demo.txt", "content": "hello tool runtime", "workspace": str(tmp_path)},
        )
    )
    assert write_response.result is not None
    assert write_response.result.output["path"].endswith("demo.txt")

    read_tool = manager.get_tool("file_read")
    read_response = read_tool.execute(
        ToolRequest(
            request_id="req-read",
            tool_id="file_read",
            payload={"path": "demo.txt", "workspace": str(tmp_path)},
        )
    )
    assert read_response.result is not None
    assert read_response.result.output["content"] == "hello tool runtime"

    scan_tool = manager.get_tool("workspace_scan")
    scan_response = scan_tool.execute(
        ToolRequest(
            request_id="req-scan",
            tool_id="workspace_scan",
            payload={"workspace": str(tmp_path)},
        )
    )
    assert scan_response.result is not None
    assert scan_response.result.output["workspace_root"] == str(tmp_path)

    plan_tool = manager.get_tool("plan_create")
    plan_response = plan_tool.execute(
        ToolRequest(
            request_id="req-plan",
            tool_id="plan_create",
            payload={"goal": "ship core tools", "workspace": str(tmp_path)},
        )
    )
    assert plan_response.result is not None
    assert plan_response.result.output["goal"] == "ship core tools"
