# Tool Creation Pipeline for SpaceTraders MCP

This document describes the standard process for adding a new tool to the SpaceTraders MCP server, ensuring correctness, completeness, and documentation at every step.

---

## Tool Creation Pipeline

### 1. Identify a Missing Tool
- Review the current `TODO.md` checklist and the official OpenAPI schema (`schemas/SpaceTraderFullAPI.json`).
- Find an endpoint that is not yet implemented as an MCP tool.
- Select a tool that is useful, feasible, and not redundant.

### 2. Implement the Tool
- Add a new MCP tool function in `src/main.py`.
- Follow the endpoint specification in the OpenAPI schema for required parameters, authentication, and response structure.
- Ensure the implementation is non-destructive to existing code.

### 3. Verify the Tool
- Compare the tool's implementation against the OpenAPI schema.
- Document the verification in `Dev/Verification.md`:
  - Mapped endpoint
  - OpenAPI reference
  - Implementation summary
  - Verification checklist
  - Conclusion and any issues or suggestions

### 4. Update the TODO List
- Mark the tool as implemented in `TODO.md`.
- Ensure the checklist accurately reflects the current state of the codebase.

### 5. Prepare for Commit
- Stage the changes (new tool, updated documentation, etc.).
- Write a commit message summarizing:
  - The tool created
  - The endpoint it implements
  - The verification and documentation steps taken
- Commit and push the changes to the repository.

---

## Example: Get_Public_Agent Tool

- Identified `GET /agents/{agentSymbol}` as missing in `TODO.md` and OpenAPI schema.
- Implemented `Get_Public_Agent` in `src/main.py`.
- Verified the tool against the schema and documented in `Dev/Verification.md`.
- Updated `TODO.md` to mark the tool as complete.
- Prepared a commit with a message detailing the tool creation and verification process.

---

**This pipeline ensures every tool is implemented, verified, and documented in a consistent and reliable manner.** 