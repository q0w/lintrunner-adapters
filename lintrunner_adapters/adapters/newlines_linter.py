"""NEWLINE: Checks files to make sure there are no trailing newlines."""

# PyTorch LICENSE. See LICENSE file in the root directory of this source tree.

from __future__ import annotations

import argparse
import logging
import sys

from lintrunner_adapters import IS_WINDOWS, LintMessage, LintSeverity

NEWLINE = 10  # ASCII "\n"
CARRIAGE_RETURN = 13  # ASCII "\r"
LINTER_CODE = "NEWLINE"


def check_file(filename: str) -> LintMessage | None:
    logging.debug("Checking file %s", filename)

    with open(filename, "rb") as f:
        lines = f.readlines()

    if not lines:
        # File is empty, just leave it alone.
        return None

    if len(lines) == len(lines[0]) == 1:
        # file is wrong whether or not the only byte is a newline
        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="testestTrailing newline",
            original=None,
            replacement=None,
            description="Trailing newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )

    if len(lines[-1]) == 1 and lines[-1][0] == NEWLINE:
        try:
            original = b"".join(lines).decode("utf-8")
        except Exception as err:
            return LintMessage(
                path=filename,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Decoding failure",
                original=None,
                replacement=None,
                description=f"utf-8 decoding failed due to {err.__class__.__name__}:\n{err}",
            )

        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="Trailing newline",
            original=original,
            replacement=original.rstrip("\n") + "\n",
            description="Trailing newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )

    # Check DOS newlines
    if IS_WINDOWS:
        # Do nothing on Windows
        return None

    has_changes = False
    original_lines: list[bytes] | None = None
    for idx, line in enumerate(lines):
        if len(line) >= 2 and line[-1] == NEWLINE and line[-2] == CARRIAGE_RETURN:
            if not has_changes:
                original_lines = lines.copy()
                has_changes = True
            lines[idx] = line[:-2] + b"\n"

    if has_changes:
        try:
            assert original_lines is not None
            original = b"".join(original_lines).decode("utf-8")
            replacement = b"".join(lines).decode("utf-8")
        except Exception as err:
            return LintMessage(
                path=filename,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Decoding failure",
                original=None,
                replacement=None,
                description=f"utf-8 decoding failed due to {err.__class__.__name__}:\n{err}",
            )
        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="DOS newline",
            original=original,
            replacement=replacement,
            description="DOS newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Checks files to make sure there are no trailing newlines. Linter code: {LINTER_CODE}",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="verbose logging",
    )
    parser.add_argument(
        "filenames",
        nargs="+",
        help="paths to lint",
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="<%(threadName)s:%(levelname)s> %(message)s",
        level=logging.NOTSET
        if args.verbose
        else logging.DEBUG
        if len(args.filenames) < 1000
        else logging.INFO,
        stream=sys.stderr,
    )

    lint_messages = []
    for filename in args.filenames:
        lint_message = check_file(filename)
        if lint_message is not None:
            lint_messages.append(lint_message)

    for lint_message in lint_messages:
        lint_message.display()
