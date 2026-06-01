from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from loguru import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.schemas.skill import MCPServerConfig, ToolInfo


class MCPClientManager:
    """Manages connections to MCP servers and provides tool discovery/invocation.

    Each MCP server is identified by a name and configured via MCPServerConfig.
    """

    def __init__(self, servers: dict[str, MCPServerConfig] | None = None):
        self._servers: dict[str, MCPServerConfig] = servers or {}

    def register_server(self, name: str, config: MCPServerConfig) -> None:
        self._servers[name] = config

    async def list_tools(self, server_name: str) -> list[ToolInfo]:
        config = self._servers.get(server_name)
        if not config:
            raise ValueError(f"Unknown MCP server: {server_name}")

        async with self._connect(config) as session:
            result = await session.list_tools()
            return [
                ToolInfo(
                    name=t.name,
                    description=t.description or "",
                    server_name=server_name,
                    input_schema=t.inputSchema if hasattr(t, "inputSchema") else {},
                )
                for t in result.tools
            ]

    async def list_all_tools(self) -> list[ToolInfo]:
        tools: list[ToolInfo] = []
        for server_name in self._servers:
            try:
                tools.extend(await self.list_tools(server_name))
            except Exception as e:
                logger.warning("Failed to list tools from {}: {}", server_name, e)
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        config = self._servers.get(server_name)
        if not config:
            raise ValueError(f"Unknown MCP server: {server_name}")

        async with self._connect(config) as session:
            result = await session.call_tool(tool_name, arguments=arguments or {})
            return result.content

    @asynccontextmanager
    async def _connect(self, config: MCPServerConfig) -> AsyncIterator[ClientSession]:
        params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env if config.env else None,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
