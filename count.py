from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class FileCount:
    path: Path
    total: int
    blank: int
    comment: int
    code: int


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
}


def iter_python_files(root: Path, exclude_dirs: set[str]) -> Iterator[Path]:
    root = root.resolve()
    if root.is_file():
        if root.suffix.lower() == ".py":
            yield root
        return

    for path in root.rglob("*.py"):
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts

        if any(part in exclude_dirs for part in relative_parts):
            continue

        yield path


def count_file_lines(file_path: Path, *, encoding: str = "utf-8") -> FileCount:
    total = blank = comment = code = 0

    try:
        text = file_path.read_text(encoding=encoding, errors="replace")
    except OSError:
        return FileCount(path=file_path, total=0, blank=0, comment=0, code=0)

    for line in text.splitlines():
        total += 1
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith("#"):
            comment += 1
        else:
            code += 1

    return FileCount(
        path=file_path, total=total, blank=blank, comment=comment, code=code
    )


def format_row(cols: list[str], widths: list[int]) -> str:
    return "  ".join(col.ljust(width) for col, width in zip(cols, widths, strict=True))


def summarize(counts: Iterable[FileCount]) -> FileCount:
    total = blank = comment = code = 0
    for c in counts:
        total += c.total
        blank += c.blank
        comment += c.comment
        code += c.code
    return FileCount(
        path=Path("<TOTAL>"), total=total, blank=blank, comment=comment, code=code
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="统计 Python 代码行数（只统计 .py 文件）",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="要统计的目录或文件路径（默认：当前目录）",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help=f"排除目录名（可重复）。默认已排除：{', '.join(sorted(DEFAULT_EXCLUDE_DIRS))}",
    )
    parser.add_argument(
        "--no-default-exclude",
        action="store_true",
        help="不使用默认排除目录列表",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="读取文件时使用的编码（默认：utf-8；无法解码会用 replacement）",
    )
    parser.add_argument(
        "--sort",
        choices=["total", "code", "comment", "blank", "path"],
        default="total",
        help="排序字段（默认：total）",
    )
    parser.add_argument(
        "--desc",
        action="store_true",
        help="倒序排序",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="只显示前 N 个文件（0 表示全部显示）",
    )
    parser.add_argument(
        "--no-per-file",
        action="store_true",
        help="不输出每个文件明细，只输出总计",
    )

    args = parser.parse_args(argv)
    root = Path(args.path)

    exclude_dirs = set()
    if not args.no_default_exclude:
        exclude_dirs |= DEFAULT_EXCLUDE_DIRS
    exclude_dirs |= set(args.exclude_dir)

    files = list(iter_python_files(root, exclude_dirs))
    counts = [count_file_lines(p, encoding=args.encoding) for p in files]

    key_map = {
        "total": lambda c: c.total,
        "code": lambda c: c.code,
        "comment": lambda c: c.comment,
        "blank": lambda c: c.blank,
        "path": lambda c: str(c.path).lower(),
    }
    counts.sort(key=key_map[args.sort], reverse=args.desc)

    if args.top and args.top > 0:
        shown = counts[: args.top]
    else:
        shown = counts

    total_count = summarize(counts)

    if not args.no_per_file:
        headers = ["File", "Total", "Code", "Comment", "Blank"]
        rows: list[list[str]] = []

        base = root.resolve() if root.exists() and root.is_dir() else None
        for c in shown:
            display_path = str(c.path)
            if base is not None:
                try:
                    display_path = str(c.path.resolve().relative_to(base))
                except ValueError:
                    display_path = str(c.path)

            rows.append(
                [
                    display_path,
                    str(c.total),
                    str(c.code),
                    str(c.comment),
                    str(c.blank),
                ]
            )

        widths = [len(h) for h in headers]
        for row in rows:
            for i, col in enumerate(row):
                widths[i] = max(widths[i], len(col))

        print(format_row(headers, widths))
        print(format_row(["-" * w for w in widths], widths))
        for row in rows:
            print(format_row(row, widths))

        if args.top and args.top > 0 and len(counts) > len(shown):
            print(f"... 省略 {len(counts) - len(shown)} 个文件")

        print()

    print(
        f"TOTAL  files={len(files)}  total={total_count.total}  code={total_count.code}  comment={total_count.comment}  blank={total_count.blank}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
