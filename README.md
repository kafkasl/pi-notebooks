# pi-notebooks

Jupyter notebook (`.ipynb`) cell-level read, edit, search, and management for [pi](https://github.com/badlogic/pi).

## Why?

Pi's built-in `read` shows `.ipynb` files as raw JSON — thousands of lines of noise. `edit` requires matching exact JSON strings. This package provides cell-level operations instead.

## Install

```bash
pi install git:github.com/kafkasl/pi-notebooks
```

## Usage

The skill auto-activates when working with `.ipynb` files, or invoke manually with `/skill:nb`.

### View notebook structure
```bash
nb view notebook.ipynb
```
```
[  0] code    (  1L) import pandas as pd
[  1] mark    (  1L) # Analysis
[  2] code 📤 ( 12L) df = pd.read_csv("data.csv")
[  3] code 📤 (  3L) df.describe()
```

### Read a cell with line numbers
```bash
nb read notebook.ipynb 2 --nums
```
```
--- Cell [2] (code) ---
   1 | df = pd.read_csv("data.csv")
   2 | df.head()
```

### Edit cell content
```bash
nb str-replace notebook.ipynb 2 "df.head()" "df.head(10)"
nb insert-line notebook.ipynb 2 0 "# Load data"
nb replace-lines notebook.ipynb 2 1 2 "new content here"
nb delete-lines notebook.ipynb 2 3
```

All edit commands print a unified diff showing what changed.

### Search across cells
```bash
nb search notebook.ipynb "def train"
```

### Add / delete cells
```bash
nb add notebook.ipynb "# New Section" --after 1 --type markdown
nb delete notebook.ipynb 5
```

### View cell output
```bash
nb output notebook.ipynb 3
```

## Commands Reference

| Command | Description |
|---|---|
| `nb view <path>` | Show all cells with index, type, line count, preview |
| `nb read <path> <idx> [--nums]` | Read cell content |
| `nb output <path> <idx>` | View cell output |
| `nb search <path> <pattern>` | Search cells by regex |
| `nb str-replace <path> <idx> <old> <new>` | String replace in cell |
| `nb replace-lines <path> <idx> <start> <end> [content]` | Replace line range |
| `nb insert-line <path> <idx> <line> <content>` | Insert at line |
| `nb delete-lines <path> <idx> <start> [end]` | Delete lines |
| `nb replace <path> <idx> <content>` | Replace entire cell |
| `nb add <path> <content> [--after N] [--type code]` | Add cell |
| `nb delete <path> <idx>` | Delete cell |

## License

MIT
