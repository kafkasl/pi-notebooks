# pi-notebooks

Jupyter notebook (`.ipynb`) cell-level read, edit, search, and management for [pi](https://github.com/badlogic/pi).

## Why?

Pi's built-in `read` shows `.ipynb` files as raw JSON — thousands of lines of noise. `edit` requires matching exact JSON strings. This package gives the LLM a proper `nb` tool that operates on cells instead.

## Install

```bash
pi install git:github.com/kafkasl/pi-notebooks
```

**Requires [uv](https://docs.astral.sh/uv/)** on PATH (the tool uses `uv run` to manage Python dependencies automatically).

After installing, run `/reload` in your pi session. The `nb` tool will be available to the LLM immediately — no skill activation needed.

## How it works

The package registers an `nb` tool that the LLM calls with typed parameters:

```
nb({ action: "view", path: "notebook.ipynb" })
nb({ action: "read", path: "notebook.ipynb", cell: 3, nums: true })
nb({ action: "str_replace", path: "notebook.ipynb", cell: 3, old: "foo", new: "bar" })
nb({ action: "create", path: "new.ipynb", content: "# Title" })
```

No shell escaping issues — content with quotes, newlines, and special characters is passed as structured data.

## Actions

### Create & browse

| Action | Parameters | Description |
|---|---|---|
| `create` | `path`, `content?` (title), `kernel?` | Create a new notebook |
| `view` | `path` | Show all cells: index, type, line count, preview |
| `read` | `path`, `cell`, `nums?` | Read cell content (use `nums: true` before editing) |
| `output` | `path`, `cell` | View cell execution output |
| `search` | `path`, `pattern` | Search cells by regex |

### Edit cell content

| Action | Parameters | Description |
|---|---|---|
| `str_replace` | `path`, `cell`, `old`, `new` | Find and replace text in a cell |
| `replace_lines` | `path`, `cell`, `start`, `end`, `content?` | Replace a line range (1-based, inclusive) |
| `insert_line` | `path`, `cell`, `line`, `content` | Insert text at line number (0 = before first) |
| `delete_lines` | `path`, `cell`, `start`, `end?` | Delete line range |
| `replace` | `path`, `cell`, `content` | Replace entire cell content |

### Add & delete cells

| Action | Parameters | Description |
|---|---|---|
| `add` | `path`, `content`, `after?`/`before?`, `type?` | Add cell (default: code) |
| `delete` | `path`, `cell` | Delete a cell |

All edit actions print a unified diff showing what changed.

## Example output

```
nb({ action: "view", path: "analysis.ipynb" })
```
```
[  0] code    (  1L) import pandas as pd
[  1] mark    (  1L) # Analysis
[  2] code 📤 ( 12L) df = pd.read_csv("data.csv")
[  3] code 📤 (  3L) df.describe()
```

The 📤 indicator shows cells that have execution output.

## Acknowledgments

Almost verbatim translation of the dialog editing tools in [dialoghelper](https://github.com/AnswerDotAI/dialoghelper) by [Answer.AI](https://www.answer.ai/) / Jeremy Howard, built for [SolveIt](https://solveit.fast.ai/). The cell-level text transforms and the read→transform→write→diff pattern are adapted from their approach.

## License

MIT
