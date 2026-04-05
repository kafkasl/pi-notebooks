---
name: nb
description: Read, edit, and manage Jupyter notebook (.ipynb) cells. Use when working with .ipynb files instead of raw read/edit.
---

# Jupyter Notebook Tool

When working with `.ipynb` files, **always use `nb` commands instead of `read`/`edit`**. Raw `.ipynb` files are JSON — `read` shows thousands of lines of noise, and `edit` requires matching exact JSON strings.

The `nb` CLI operates on cells by index, showing clean source content.

## Commands

All commands: `python3 {baseDir}/nb.py <command> [args]`

### Create a notebook
```bash
python3 {baseDir}/nb.py create <path>                          # empty notebook
python3 {baseDir}/nb.py create <path> --title "# My Notebook"  # with title cell
```

### View notebook structure
```bash
python3 {baseDir}/nb.py view <path>
```
Shows all cells: index, type (code/mark/raw), output indicator (📤), line count, first-line preview.

### Read a cell
```bash
python3 {baseDir}/nb.py read <path> <cell_idx>           # plain
python3 {baseDir}/nb.py read <path> <cell_idx> --nums     # with line numbers
```
**Always use `--nums` before editing** to get accurate line numbers.

### View cell output
```bash
python3 {baseDir}/nb.py output <path> <cell_idx>
```

### Search cells by regex
```bash
python3 {baseDir}/nb.py search <path> "<pattern>"
```
Shows matching cells with line numbers of matches.

### Edit cell content

**String replace** (best for small targeted changes):
```bash
python3 {baseDir}/nb.py str-replace <path> <cell_idx> "<old>" "<new>"
```

**Replace lines** (best for replacing blocks, 1-based inclusive):
```bash
python3 {baseDir}/nb.py replace-lines <path> <cell_idx> <start> <end> "<new_content>"
```

**Insert line** (0 = before first line, 1 = after first line):
```bash
python3 {baseDir}/nb.py insert-line <path> <cell_idx> <line_num> "<content>"
```

**Delete lines** (1-based, inclusive):
```bash
python3 {baseDir}/nb.py delete-lines <path> <cell_idx> <start> [end]
```

**Replace entire cell**:
```bash
python3 {baseDir}/nb.py replace <path> <cell_idx> "<content>"
```

### Add / delete cells

```bash
python3 {baseDir}/nb.py add <path> "<content>" --after <idx> --type code
python3 {baseDir}/nb.py add <path> "<content>" --before <idx> --type markdown
python3 {baseDir}/nb.py delete <path> <cell_idx>
```
Type defaults to `code`. Omitting `--after`/`--before` appends to end.

## Workflow

1. `nb view` to see notebook structure
2. `nb read <idx> --nums` to inspect a cell with line numbers
3. Edit with `str-replace`, `replace-lines`, `insert-line`, or `delete-lines`
4. All edit commands print a unified diff showing what changed

## Important

- All edit commands produce diffs — verify the diff before continuing
- Cell indices shift after `add`/`delete` — re-run `view` if needed
- Shell quoting: for content with quotes/newlines, use heredocs or `$'...'` syntax
