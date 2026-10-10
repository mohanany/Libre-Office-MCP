"""Console-script entry points for single-app MCP servers."""

from __future__ import annotations

from .server import run_app


def writer() -> None:
    run_app("writer")


def calc() -> None:
    run_app("calc")


def impress() -> None:
    run_app("impress")


def draw() -> None:
    run_app("draw")


def base() -> None:
    run_app("base")


def math() -> None:
    run_app("math")
