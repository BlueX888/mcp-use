"""
Unit tests for search_tools when a tool has no description.

`mcp.types.Tool.description` is Optional (`str | None = None`), so servers may
legally list tools without a description. Both `MCPClient.search_tools` and the
code-mode `search_tools` function must treat such tools as having an empty
description instead of raising an AttributeError while filtering by query.
"""

from unittest.mock import AsyncMock, MagicMock

from mcp.types import Tool

from mcp_use.client.client import MCPClient
from mcp_use.client.code_executor import CodeExecutor


def _make_tool(name: str, description: str | None) -> Tool:
    return Tool(name=name, description=description, inputSchema={"type": "object"})


def _make_client(tools: list[Tool]) -> MCPClient:
    client = MCPClient(config={"mcpServers": {}})
    session = MagicMock()
    session.list_tools = AsyncMock(return_value=tools)
    client.sessions["test_server"] = session
    return client


class TestSearchToolsNoneDescription:
    """Test search_tools with tools whose description is None."""

    async def test_search_tools_full_with_none_description(self):
        """Filtering with query must not crash when a tool has description=None."""
        client = _make_client([_make_tool("echo", None)])

        result = await client.search_tools("echo")

        assert result["meta"]["total_tools"] == 1
        assert result["meta"]["result_count"] == 1
        assert result["results"][0]["name"] == "echo"
        assert result["results"][0]["description"] == ""

    async def test_search_tools_descriptions_detail_level_with_none_description(self):
        """The "descriptions" detail level must also handle description=None."""
        client = _make_client([_make_tool("echo", None)])

        result = await client.search_tools("echo", detail_level="descriptions")

        assert result["meta"]["result_count"] == 1
        assert result["results"][0]["description"] == ""

    async def test_search_tools_description_match_still_works(self):
        """Tools with a real description must still match by description text."""
        client = _make_client(
            [
                _make_tool("find_user", "Find a user by email"),
                _make_tool("echo", None),
            ]
        )

        result = await client.search_tools("email")

        assert result["meta"]["result_count"] == 1
        assert result["results"][0]["name"] == "find_user"

    async def test_search_tools_none_description_not_matched(self):
        """A tool without description must simply not match an unrelated query."""
        client = _make_client([_make_tool("echo", None)])

        result = await client.search_tools("nonexistent")

        assert result["meta"]["total_tools"] == 1
        assert result["meta"]["result_count"] == 0
        assert result["results"] == []


class TestCodeModeSearchToolsNoneDescription:
    """Test the code-mode search_tools function with description=None tools."""

    def _make_executor(self, tools: list[Tool]) -> CodeExecutor:
        mock_client = MagicMock(spec=MCPClient)
        mock_client.code_mode = True
        session = MagicMock()
        session.list_tools = AsyncMock(return_value=tools)
        mock_client.sessions = {"test_server": session}
        return CodeExecutor(mock_client)

    async def test_code_mode_search_tools_with_none_description(self):
        """Code-mode search_tools must not crash on description=None tools."""
        executor = self._make_executor(
            [
                _make_tool("find_user", "Find a user by email"),
                _make_tool("echo", None),
            ]
        )

        result = await executor.execute(
            """
result = await search_tools("echo")
return {"count": result['meta']['result_count'], "descriptions": [t['description'] for t in result['results']]}
""",
            timeout=5.0,
        )

        assert result["error"] is None
        assert result["result"]["count"] == 1
        assert result["result"]["descriptions"] == [""]
