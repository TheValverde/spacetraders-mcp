# SpaceTraders MCP Server

A Model Context Protocol (MCP) server for interacting with the [SpaceTraders API](https://spacetraders.io/). This server exposes SpaceTraders API endpoints as MCP tools, allowing AI agents to manage agents, fleets, contracts, and trading operations in the SpaceTraders universe.

## Overview

This project provides an MCP server that enables AI agents to:
- Register and manage SpaceTraders agents
- View and manage ships and fleets
- Accept, deliver, and fulfill contracts
- Trade resources and interact with markets
- Explore systems, waypoints, and shipyards

The implementation is based on the [MCP](https://modelcontextprotocol.io) standard, using the `mcp` Python package for server infrastructure.

## Features

- Register new SpaceTraders agents
- View agent details and list agents
- List, view, accept, deliver, and fulfill contracts
- List ships, view ship details, purchase ships
- Navigate, dock, orbit, refuel, and extract resources with ships
- Transfer and sell cargo
- Scan systems, waypoints, and ships
- View markets and shipyards
- Chart waypoints and refine resources

See `TODO.md` for a detailed checklist of implemented and missing endpoints.

## Prerequisites

- Python 3.12+
- SpaceTraders API key (from https://my.spacetraders.io)
- Docker (optional, for containerized deployment)

## Installation

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/TheValverde/spacetraders-mcp.git
   cd spacetraders-mcp
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Create a `.env` file in the project root and add your SpaceTraders API key:
   ```env
   SPACETRADERS_API_KEY=your-api-key-here
   ```

### Using Docker (optional)

1. Build the Docker image:
   ```bash
   docker build -t spacetraders-mcp .
   ```

2. Create a `.env` file in the project root and add your SpaceTraders API key.

## Configuration

The following environment variable is required:

| Variable                | Description                                 |
|-------------------------|---------------------------------------------|
| `SPACETRADERS_API_KEY`  | Your SpaceTraders account token             |

## Running the Server

### Using uv

```bash
uv run src/main.py
```

### Using Docker

```bash
docker run --env-file .env -p 8050:8050 spacetraders-mcp
```

## MCP Integration

This server exposes SpaceTraders API endpoints as MCP tools. You can connect to it from any MCP-compatible client. Example configuration (update URL/port as needed):

```json
{
  "mcpServers": {
    "spacetraders": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

## Project Structure

- `src/main.py` — Main MCP server implementation and tool definitions
- `src/spacetraders_utils.py` — SpaceTraders API client and token management
- `src/utils.py` — Utility functions
- `agent_tokens.json` — Persistent agent tokens (auto-managed)
- `schemas/` — OpenAPI and reference JSON files for SpaceTraders API
- `public/` — Static assets
- `TODO.md` — Endpoint implementation checklist

## Schemas and Reference Data

The `schemas/` directory contains large JSON files used for reference and development:

- `schemas/SpaceTraders.json` — The official OpenAPI specification for the SpaceTraders API (v2). Used for endpoint reference and validation.
- `schemas/SpaceTraderFullAPI.json` — (Describe usage here if different, or remove if unused.)

These files are not required for running the server, but are useful for development, code generation, and documentation.

## Development Status

See `TODO.md` for a list of implemented and missing endpoints. The core gameplay and trading endpoints are implemented; some advanced features are still TODO.

---

This project is licensed under the terms described in the LICENSE file included in this repository. 