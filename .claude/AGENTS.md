<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# .claude

## Purpose
Claude Code framework configuration directory. Contains project-level settings and the OnFly Finance OAuth MCP (Model Context Protocol) server skill used for authenticating with OnFly APIs during development.

## Key Files

| File | Description |
|------|-------------|
| `settings.json` | Claude Code project settings — hooks, permissions, and tool configuration |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `onfly-oauth-skill/` | Node.js MCP server that handles OnFly Finance OAuth 2.0 authentication |

## For AI Agents

### Working In This Directory
- Do not modify `settings.json` unless explicitly asked to configure Claude Code behavior
- The `onfly-oauth-skill/` is an MCP server — it runs as a subprocess; changes require restarting the MCP connection
- Direct writes to `.claude/**` are allowed per OMC model routing rules

### Common Patterns
- MCP server entry point: `onfly-oauth-skill/mcp-server.js` or `server.js`
- Configuration declared in `onfly-oauth-skill/.mcp.json`

## Dependencies

### External
- Node.js runtime — required for the OAuth MCP server
- OnFly Finance OAuth 2.0 endpoints

<!-- MANUAL: -->
