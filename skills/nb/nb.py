#!/usr/bin/env python3
"""nb - Jupyter notebook CLI for structured cell access."""

import json, re, sys, difflib, textwrap
from pathlib import Path

# --- Notebook I/O ---

def load_nb(path):
    with open(path) as f: return json.load(f)

def save_nb(nb, path):
    with open(path, 'w') as f: json.dump(nb, f, indent=1, ensure_ascii=False)
    # normalize trailing newline
    p = Path(path)
    txt = p.read_text()
    if not txt.endswith('\n'): p.write_text(txt + '\n')

def cell_source(cell): return ''.join(cell['source'])
def cell_output_text(cell):
    """Extract text from cell outputs."""
    parts = []
    for out in cell.get('outputs', []):
        if 'text' in out: parts.append(''.join(out['text']))
        elif 'data' in out:
            d = out['data']
            for k in ('text/plain', 'text/html', 'text/markdown'):
                if k in d:
                    parts.append(''.join(d[k]))
                    break
    return '\n'.join(parts)

# --- Pure text transforms (adapted from dialoghelper) ---

def str_replace(text, old, new, start_line=None, end_line=None):
    """Replace old with new in text, optionally within line range."""
    if start_line or end_line:
        lines = text.splitlines(True)
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        region = ''.join(lines[s:e])
        if old not in region:
            raise ValueError(f"Text not found in lines {s+1}-{e}: {repr(old)}")
        return ''.join(lines[:s]) + region.replace(old, new) + ''.join(lines[e:])
    if old not in text:
        raise ValueError(f"Text not found: {repr(old)}")
    return text.replace(old, new)

def insert_line(text, line_num, new_str):
    """Insert new_str after line_num (0 = before first line)."""
    lines = text.splitlines()
    if not (0 <= line_num <= len(lines)):
        raise ValueError(f'Invalid line {line_num}. Valid: 0-{len(lines)}')
    lines.insert(line_num, new_str)
    return '\n'.join(lines)

def replace_lines(text, start, end=None, new_content=''):
    """Replace lines start..end (1-based, inclusive) with new_content."""
    lines = text.splitlines(keepends=True)
    if end is None: end = start
    if end < 0: end = len(lines) + end + 1
    if not (1 <= start <= len(lines)):
        raise ValueError(f'Invalid start {start}. Valid: 1-{len(lines)}')
    if not (start <= end <= len(lines)):
        raise ValueError(f'Invalid end {end}. Valid: {start}-{len(lines)}')
    if new_content and not new_content.endswith('\n'): new_content += '\n'
    lines[start-1:end] = [new_content] if new_content else []
    return ''.join(lines)

def delete_lines(text, start, end=None):
    """Delete lines start..end (1-based, inclusive)."""
    return replace_lines(text, start, end, '')

# --- Diff helper ---

def show_diff(old, new):
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=1, lineterm=''))
    return '\n'.join(d[2:]) if len(d) > 2 else 'No changes.'

# --- Cell edit wrapper ---

def edit_cell(nb, path, idx, transform_fn, *args, **kwargs):
    """Read cell source, apply transform, write back, show diff."""
    cell = nb['cells'][idx]
    old = cell_source(cell)
    try:
        new = transform_fn(old, *args, **kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    diff = show_diff(old, new)
    cell['source'] = new.splitlines(True)
    # fix last line to not have trailing newline (ipynb convention)
    if cell['source'] and cell['source'][-1].endswith('\n'):
        cell['source'][-1] = cell['source'][-1][:-1]
    save_nb(nb, path)
    print(diff)

# --- Commands ---

def cmd_view(path, **kw):
    """Show all cells: index, type, preview."""
    nb = load_nb(path)
    for i, c in enumerate(nb['cells']):
        src = cell_source(c).strip()
        typ = c['cell_type'][:4]
        first_line = src.split('\n')[0][:120] if src else '(empty)'
        n_lines = len(src.splitlines())
        has_out = '📤' if c.get('outputs') else '  '
        print(f"[{i:3d}] {typ:4s} {has_out} ({n_lines:3d}L) {first_line}")

def cmd_read(path, idx, nums=False, **kw):
    """Read cell content, optionally with line numbers."""
    nb = load_nb(path)
    idx = int(idx)
    cell = nb['cells'][idx]
    src = cell_source(cell)
    typ = cell['cell_type']
    print(f"--- Cell [{idx}] ({typ}) ---")
    if nums:
        for i, line in enumerate(src.splitlines(), 1):
            print(f"{i:4d} | {line}")
    else:
        print(src)

def cmd_output(path, idx, **kw):
    """View cell output."""
    nb = load_nb(path)
    idx = int(idx)
    cell = nb['cells'][idx]
    out = cell_output_text(cell)
    if out:
        print(f"--- Output [{idx}] ---")
        print(out)
    else:
        print(f"Cell [{idx}] has no output.")

def cmd_search(path, pattern, **kw):
    """Search cells by regex pattern."""
    nb = load_nb(path)
    pat = re.compile(pattern, re.MULTILINE | re.DOTALL)
    for i, c in enumerate(nb['cells']):
        src = cell_source(c)
        matches = list(pat.finditer(src))
        if matches:
            typ = c['cell_type'][:4]
            first = src.strip().split('\n')[0][:100]
            print(f"[{i:3d}] {typ:4s} ({len(matches)} match) {first}")
            for m in matches[:3]:
                # show the line containing the match
                line_start = src.rfind('\n', 0, m.start()) + 1
                line_end = src.find('\n', m.end())
                if line_end == -1: line_end = len(src)
                line_num = src[:m.start()].count('\n') + 1
                print(f"       L{line_num}: {src[line_start:line_end].strip()[:120]}")

def cmd_add(path, content, after=None, before=None, type='code', **kw):
    """Add a new cell."""
    nb = load_nb(path)
    cell = {'cell_type': type, 'metadata': {}, 'source': content.splitlines(True)}
    if type == 'code':
        cell['execution_count'] = None
        cell['outputs'] = []
    if after is not None:
        pos = int(after) + 1
    elif before is not None:
        pos = int(before)
    else:
        pos = len(nb['cells'])
    nb['cells'].insert(pos, cell)
    save_nb(nb, path)
    print(f"Added {type} cell at [{pos}]")

def cmd_delete(path, idx, **kw):
    """Delete a cell."""
    nb = load_nb(path)
    idx = int(idx)
    cell = nb['cells'].pop(idx)
    save_nb(nb, path)
    typ = cell['cell_type']
    src = cell_source(cell).strip().split('\n')[0][:80]
    print(f"Deleted [{idx}] {typ}: {src}")

def cmd_edit_str_replace(path, idx, old, new, **kw):
    nb = load_nb(path)
    edit_cell(nb, path, int(idx), str_replace, old, new)

def cmd_edit_replace_lines(path, idx, start, end, content='', **kw):
    nb = load_nb(path)
    edit_cell(nb, path, int(idx), replace_lines, int(start), int(end), content)

def cmd_edit_insert_line(path, idx, line, content, **kw):
    nb = load_nb(path)
    edit_cell(nb, path, int(idx), insert_line, int(line), content)

def cmd_edit_delete_lines(path, idx, start, end=None, **kw):
    nb = load_nb(path)
    end = int(end) if end else None
    edit_cell(nb, path, int(idx), delete_lines, int(start), end)

def cmd_replace(path, idx, content, **kw):
    """Replace entire cell content."""
    nb = load_nb(path)
    idx = int(idx)
    old = cell_source(nb['cells'][idx])
    nb['cells'][idx]['source'] = content.splitlines(True)
    if nb['cells'][idx]['source'] and nb['cells'][idx]['source'][-1].endswith('\n'):
        nb['cells'][idx]['source'][-1] = nb['cells'][idx]['source'][-1][:-1]
    save_nb(nb, path)
    print(show_diff(old, content))

# --- CLI dispatch ---

USAGE = """nb - Jupyter notebook CLI

Usage:
  nb view <path>                                     Show all cells
  nb read <path> <idx> [--nums]                      Read cell content
  nb output <path> <idx>                             View cell output
  nb search <path> <pattern>                         Search cells by regex
  nb add <path> <content> [--after N] [--type code]  Add cell
  nb delete <path> <idx>                             Delete cell
  nb replace <path> <idx> <content>                  Replace entire cell
  nb str-replace <path> <idx> <old> <new>            String replace in cell
  nb replace-lines <path> <idx> <start> <end> [content]  Replace line range
  nb insert-line <path> <idx> <line> <content>       Insert at line
  nb delete-lines <path> <idx> <start> [end]         Delete lines"""

def parse_flag(args, flag, default=None, is_bool=False):
    """Extract --flag value from args list, mutating args."""
    for i, a in enumerate(args):
        if a == flag:
            if is_bool:
                args.pop(i)
                return True
            if i + 1 < len(args):
                args.pop(i)
                return args.pop(i)
    return default

def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(USAGE); return

    cmd = args.pop(0)

    if cmd == 'view':
        cmd_view(args[0])
    elif cmd == 'read':
        nums = parse_flag(args, '--nums', is_bool=True)
        cmd_read(args[0], args[1], nums=nums)
    elif cmd == 'output':
        cmd_output(args[0], args[1])
    elif cmd == 'search':
        cmd_search(args[0], args[1])
    elif cmd == 'add':
        after = parse_flag(args, '--after')
        before = parse_flag(args, '--before')
        typ = parse_flag(args, '--type', 'code')
        cmd_add(args[0], args[1], after=after, before=before, type=typ)
    elif cmd == 'delete':
        cmd_delete(args[0], args[1])
    elif cmd == 'replace':
        cmd_replace(args[0], args[1], args[2])
    elif cmd == 'str-replace':
        cmd_edit_str_replace(args[0], args[1], args[2], args[3])
    elif cmd == 'replace-lines':
        content = args[4] if len(args) > 4 else ''
        cmd_edit_replace_lines(args[0], args[1], args[2], args[3], content)
    elif cmd == 'insert-line':
        cmd_edit_insert_line(args[0], args[1], args[2], args[3])
    elif cmd == 'delete-lines':
        end = args[3] if len(args) > 3 else None
        cmd_edit_delete_lines(args[0], args[1], args[2], end)
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)

if __name__ == '__main__':
    main()
