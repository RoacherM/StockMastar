# Python Agentic Engineering Preferences

## 0. The Ambiguity Protocol (Supreme Law)

**"Stop, Ask, Then Architect."** — Embracing **KISS: Keep It Simple, Stupid.**

### Schema First (No Guessing, No Defending)
* When data structures are unclear (API payloads, nested Dicts, config keys):
    * **HALT:** Do not guess. Do not write defensive `try/except` or `.get()` wrappers "just in case".
    * **ACTION:** Request the schema, Pydantic model, or sample payload **before writing any code**.
* **Rationale:** Defensive code for unknown structures creates hidden bugs. Clarity upfront eliminates them.

### KISS Mandate
* **Simplest Solution First:** Always propose the most straightforward implementation. Add complexity only when a concrete requirement demands it.
* **No Speculative Abstraction:** Do not create abstract base classes, factory patterns, or plugin systems unless explicitly requested.
* **Flat > Nested:** Prefer flat data structures and shallow call stacks.

### Destructive Safety
* For operations involving **file deletion**, **overwriting**, or **high-cost API usage**:
    * **ACTION:** Propose an execution plan and **wait for confirmation** before implementing.

### Logic Confirmation
* When business logic is vague (e.g., "how to handle codec incompatibilities"), propose a strategy and wait for approval.

---

## I. Architecture: The "Soul & Body" Pattern

### The "Soul" (Core Logic)
* **Pure & Stateless:** Core functions/classes should handle logic and return **Objects/Generators**.
* **No Print Statements:** Business logic must **NOT** contain `print()`. Emit events, logs, or yield status updates.
* **Data Contracts:** Replace `Dict[str, Any]` with **`pydantic.BaseModel`**. This is the single most important rule for stability.

### The "Body" (CLI/Interface)
* **Visual Rendering:** The layer that calls the "Soul". Handles `print`, `Rich` rendering, and user interaction.
* **Lazy Loading:** For CLI tools, import heavy libraries (like `pandas`, `torch`, `ffmpeg`) **inside the function** to ensure instant startup speed.

### Configuration as Code
* Separate code from config. Use `.env` files with `pydantic-settings` instead of hardcoded constants.

---

## II. Modern Tooling & Performance

### `uv` Standard
* Assume the project is managed by **`uv`**. Dependencies must be explicit in `pyproject.toml`.

### Async Native (Network I/O)
* For **LLM APIs** and **File Downloads**, strictly use **`async/await`** with **`httpx`** or **`aiohttp`**. Synchronous `requests` is banned for Agentic workflows.

### Path Safety
* **`pathlib.Path`** is mandatory. No string manipulation for paths.

---

## III. Coding Idioms

### Explicit Over Defensive
* **Banned Pattern:** Writing `.get('key', default)` or `try/except KeyError` to "handle" unknown dict structures.
* **Required Pattern:** Define a `pydantic.BaseModel` first. Let validation fail loudly at the boundary.
* **Example:**
  ```python
  # ❌ Defensive (hides bugs)
  url = data.get('url', '')
  if not url:
      logger.warning("Missing url")

  # ✅ Explicit (fails fast, schema-driven)
  class Payload(BaseModel):
      url: HttpUrl

  payload = Payload(**data)  # Fails immediately if invalid
  ```