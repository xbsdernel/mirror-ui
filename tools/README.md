# Node Toolchain (Person 2 / Epic 16)

This directory contains standalone Node.js subprocess tools invoked by the Python ADK agents:

- `babel_validate.js` (ISSUE-037): AST parsing using `@babel/parser` with `errorRecovery: true`.
- `vite_render.mjs` (ISSUE-038): Boots Vite dev server for rendering generated React code.
- `playwright_shoot.mjs` (ISSUE-039): Headless browser screenshot capture at specified viewport.

Each tool reads JSON from stdin or arguments and prints structured JSON to stdout.
