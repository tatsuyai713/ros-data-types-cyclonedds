#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: patch_type_name.py <header> <subdir> <idl_basename>", file=sys.stderr)
        return 2

    header = Path(sys.argv[1])
    subdir = re.escape(sys.argv[2])
    idl_basename = re.escape(sys.argv[3])

    text = header.read_text()
    patched = re.sub(
        rf'(return\s*")([A-Za-z0-9_]+::{subdir}::)({idl_basename})(";)',
        r'\1\2dds_::\3_\4',
        text,
    )

    if patched != text:
        header.write_text(patched)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
