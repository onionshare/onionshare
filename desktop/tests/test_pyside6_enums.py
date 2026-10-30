"""Guard against deprecated PySide6 shortcut-enum access (issue #1881).

PySide6 (like Qt 6) keeps the pre-6.4 unscoped enum spelling around for
compatibility, e.g. ``Qt.AlignLeft`` for ``Qt.AlignmentFlag.AlignLeft``. Those
shortcuts are deprecated and are slated for removal, so the desktop package
must only use the scoped spelling. This module walks the package and fails on
any shortcut access, resolving imports and introspecting the installed
PySide6 so the check follows the Qt version in use.
"""

import ast
import enum
import importlib
from pathlib import Path

PYSIDE_MODULES = (
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtNetwork",
    "QtSvg",
    "QtDBus",
)

# Enum types that are themselves deprecated in favour of another type.
DEPRECATED_ENUM_TYPES = {
    "Qt.Modifier": "Qt.KeyboardModifier",
}

DESKTOP_DIR = Path(__file__).resolve().parent.parent
SCAN_DIRS = (DESKTOP_DIR / "onionshare", DESKTOP_DIR / "tests")


def _qt_modules():
    modules = {}
    for name in PYSIDE_MODULES:
        try:
            modules[name] = importlib.import_module(f"PySide6.{name}")
        except ImportError:
            continue
    return modules


Q_MODULES = _qt_modules()


def _imported_names(tree):
    """Map each local name to the PySide6 object it refers to."""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "PySide6":
                for alias in node.names:
                    if alias.name in Q_MODULES:
                        names[alias.asname or alias.name] = Q_MODULES[alias.name]
            elif node.module.startswith("PySide6."):
                try:
                    base = importlib.import_module(node.module)
                except ImportError:
                    continue
                for alias in node.names:
                    if hasattr(base, alias.name):
                        names[alias.asname or alias.name] = getattr(base, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("PySide6."):
                    try:
                        names[alias.asname or alias.name] = importlib.import_module(
                            alias.name
                        )
                    except ImportError:
                        continue
    return names


def _attribute_chain(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return list(reversed(parts))


def _deprecated_access(parts, names):
    """Return ``(suggested, reason)`` if the chain uses a deprecated name."""
    if not parts or len(parts) < 2 or parts[0] not in names:
        return None

    obj = names[parts[0]]
    for attr in parts[1:-1]:
        if not hasattr(obj, attr):
            return None
        obj = getattr(obj, attr)
    if not hasattr(obj, parts[-1]):
        return None

    # Already scoped, e.g. QtCore.QEvent.Type.KeyPress.
    if isinstance(obj, type) and issubclass(obj, enum.Enum):
        replacement = DEPRECATED_ENUM_TYPES.get(obj.__qualname__)
        if replacement:
            prefix = ".".join(parts[:-1])
            return f"{prefix}.{replacement}.{parts[-1]}", "deprecated enum type"
        return None

    # Unscoped shortcut, e.g. QtCore.Qt.AlignCenter.
    value = getattr(obj, parts[-1])
    if not isinstance(value, enum.Enum):
        return None
    if not type(value).__qualname__.startswith(obj.__name__ + "."):
        return None
    prefix = ".".join(parts[:-1])
    return (
        f"{prefix}.{type(value).__name__}.{value.name}",
        "unscoped enum shortcut",
    )


def find_deprecated_enum_accesses():
    """Return a list of ``(path, line, expression, suggestion)`` violations."""
    violations = []
    for directory in SCAN_DIRS:
        for path in sorted(directory.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            names = _imported_names(tree)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute):
                    continue
                parts = _attribute_chain(node)
                found = _deprecated_access(parts, names)
                if found:
                    suggestion, reason = found
                    violations.append(
                        (
                            path.relative_to(DESKTOP_DIR),
                            node.lineno,
                            ".".join(parts),
                            suggestion,
                            reason,
                        )
                    )
    return violations


def test_no_deprecated_pyside6_enum_accesses():
    violations = find_deprecated_enum_accesses()
    if violations:
        report = "\n".join(
            f"  {path}:{line}: {expression} -> {suggestion} ({reason})"
            for path, line, expression, suggestion, reason in violations
        )
        raise AssertionError(
            f"{len(violations)} deprecated PySide6 enum accesses found; use the "
            f"scoped spelling instead:\n{report}"
        )
