/**
 * nb - Jupyter notebook cell-level tool for pi
 *
 * Thin wrapper that registers an `nb` tool and shells out to nb.py via `uv run`.
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { truncateHead, DEFAULT_MAX_BYTES, DEFAULT_MAX_LINES, formatSize } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { StringEnum } from "@mariozechner/pi-ai";
import { Text } from "@mariozechner/pi-tui";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const NB_PY = resolve(dirname(fileURLToPath(import.meta.url)), "..", "skills", "nb", "nb.py");

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "nb",
    label: "Notebook",
    description: `Cell-level read, edit, search, and management for Jupyter notebooks (.ipynb).
Always use this tool instead of read/edit/write for .ipynb files.`,
    promptSnippet:
      "Cell-level read/edit/search for .ipynb notebooks. Use instead of read/edit on .ipynb files.",
    promptGuidelines: [
      "When working with .ipynb files, ALWAYS use the `nb` tool instead of `read`, `edit`, or `write`.",
      "Use action 'view' first to see notebook structure, then 'read' with nums=true before editing.",
      "All edit actions (str_replace, replace_lines, insert_line, delete_lines) print a unified diff.",
    ],
    parameters: Type.Object({
      action: StringEnum([
        "create",
        "view",
        "read",
        "output",
        "search",
        "add",
        "delete",
        "replace",
        "str_replace",
        "replace_lines",
        "insert_line",
        "delete_lines",
      ] as const),
      path: Type.String({ description: "Path to the .ipynb file" }),
      cell: Type.Optional(
        Type.Number({ description: "Cell index (required for read/output/edit/delete)" })
      ),
      content: Type.Optional(
        Type.String({
          description: "Cell content (for add/replace/insert_line/replace_lines) or title (for create)",
        })
      ),
      old: Type.Optional(Type.String({ description: "Text to find (for str_replace)" })),
      new: Type.Optional(Type.String({ description: "Replacement text (for str_replace)" })),
      pattern: Type.Optional(Type.String({ description: "Regex pattern (for search)" })),
      line: Type.Optional(
        Type.Number({ description: "Line number (for insert_line: 0=before first)" })
      ),
      start: Type.Optional(Type.Number({ description: "Start line, 1-based (for replace_lines/delete_lines)" })),
      end: Type.Optional(Type.Number({ description: "End line, 1-based inclusive (for replace_lines/delete_lines)" })),
      after: Type.Optional(Type.Number({ description: "Insert after this cell index (for add)" })),
      before: Type.Optional(Type.Number({ description: "Insert before this cell index (for add)" })),
      type: Type.Optional(
        StringEnum(["code", "markdown", "raw"] as const, {
          description: "Cell type (for add, default: code)",
        })
      ),
      nums: Type.Optional(Type.Boolean({ description: "Show line numbers (for read)" })),
      kernel: Type.Optional(Type.String({ description: "Kernel name (for create, default: python3)" })),
    }),

    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const args = buildArgs(params, ctx.cwd);
      const result = await pi.exec("uv", ["run", NB_PY, ...args], {
        signal,
        timeout: 30000,
      });

      if (result.code !== 0) {
        throw new Error(result.stderr || result.stdout || `nb exited with code ${result.code}`);
      }

      let output = result.stdout;
      const truncation = truncateHead(output, {
        maxLines: DEFAULT_MAX_LINES,
        maxBytes: DEFAULT_MAX_BYTES,
      });
      if (truncation.truncated) {
        output = truncation.content;
        output += `\n\n[Truncated: ${truncation.outputLines}/${truncation.totalLines} lines, ${formatSize(truncation.outputBytes)}/${formatSize(truncation.totalBytes)}]`;
      }

      return {
        content: [{ type: "text", text: output }],
        details: { action: params.action, path: params.path },
      };
    },

    renderCall(args, theme, _context) {
      let text = theme.fg("toolTitle", theme.bold("nb "));
      text += theme.fg("accent", args.action);
      if (args.path) text += " " + theme.fg("muted", args.path);
      if (args.cell !== undefined) text += " " + theme.fg("dim", `[${args.cell}]`);
      if (args.pattern) text += " " + theme.fg("dim", `/${args.pattern}/`);
      return new Text(text, 0, 0);
    },
  });
}

/** Map typed params to CLI args for nb.py */
function buildArgs(params: Record<string, any>, cwd: string): string[] {
  const action: string = params.action;
  // Resolve path relative to cwd
  const path = resolve(cwd, params.path);

  // Map action names: underscores → hyphens for the CLI
  const cliAction = action.replace(/_/g, "-");

  switch (action) {
    case "create": {
      const args = [cliAction, path];
      if (params.content) args.push("--title", params.content);
      if (params.kernel) args.push("--kernel", params.kernel);
      return args;
    }
    case "view":
      return [cliAction, path];
    case "read": {
      const args = [cliAction, path, String(params.cell)];
      if (params.nums) args.push("--nums");
      return args;
    }
    case "output":
      return [cliAction, path, String(params.cell)];
    case "search":
      return [cliAction, path, params.pattern];
    case "add": {
      const args = [cliAction, path, params.content];
      if (params.after !== undefined) args.push("--after", String(params.after));
      if (params.before !== undefined) args.push("--before", String(params.before));
      if (params.type) args.push("--type", params.type);
      return args;
    }
    case "delete":
      return [cliAction, path, String(params.cell)];
    case "replace":
      return [cliAction, path, String(params.cell), params.content];
    case "str_replace":
      return ["str-replace", path, String(params.cell), params.old, params.new];
    case "replace_lines": {
      const args = ["replace-lines", path, String(params.cell), String(params.start), String(params.end)];
      if (params.content) args.push(params.content);
      return args;
    }
    case "insert_line":
      return ["insert-line", path, String(params.cell), String(params.line), params.content];
    case "delete_lines": {
      const args = ["delete-lines", path, String(params.cell), String(params.start)];
      if (params.end !== undefined) args.push(String(params.end));
      return args;
    }
    default:
      return [cliAction, path];
  }
}
