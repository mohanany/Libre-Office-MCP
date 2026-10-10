"""UNO bridge: connect the MCP server process to a running LibreOffice.

Connects to a soffice instance listening on a UNO socket. If none is
reachable, one is spawned (headless by default, or with GUI when
LO_MCP_GUI=1).

Environment:
    LO_MCP_HOST     socket host (default: localhost)
    LO_MCP_PORT     socket port (default: 2002)
    LO_MCP_GUI      "1" to run LibreOffice with a visible GUI
    SOFFICE_BIN     path to soffice binary (default: found on PATH)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue


def _prop(name: str, value) -> PropertyValue:
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


class OfficeBridge:
    """Lazily establishes and holds a UNO connection to LibreOffice."""

    def __init__(self) -> None:
        self.host = os.environ.get("LO_MCP_HOST", "localhost")
        self.port = int(os.environ.get("LO_MCP_PORT", "2002"))
        self._ctx = None
        self._proc: subprocess.Popen | None = None

    # -- connection ------------------------------------------------------

    def _resolve(self):
        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_ctx
        )
        url = (
            f"uno:socket,host={self.host},port={self.port};urp;"
            "StarOffice.ComponentContext"
        )
        return resolver.resolve(url)

    def connect(self, retries: int = 1, delay: float = 0.5):
        for attempt in range(retries):
            try:
                self._ctx = self._resolve()
                return self._ctx
            except Exception:
                if attempt < retries - 1:
                    time.sleep(delay)
        raise ConnectionError(
            f"cannot reach LibreOffice on {self.host}:{self.port}"
        )

    def ensure_started(self):
        """Connect, spawning a soffice listener if necessary."""
        try:
            return self.connect()
        except ConnectionError:
            pass

        soffice = os.environ.get("SOFFICE_BIN") or shutil.which("soffice") \
            or shutil.which("libreoffice")
        if not soffice:
            raise RuntimeError(
                "LibreOffice not running and no soffice binary found on PATH"
            )

        args = [
            soffice,
            f"--accept=socket,host={self.host},port={self.port};urp;",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
        ]
        if os.environ.get("LO_MCP_GUI") != "1":
            args.append("--headless")

        self._proc = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        try:
            return self.connect(retries=60, delay=1.0)
        except ConnectionError as exc:
            raise RuntimeError(
                "LibreOffice spawned but UNO socket never came up"
            ) from exc

    # -- shortcuts -------------------------------------------------------

    @property
    def ctx(self):
        if self._ctx is None:
            self.ensure_started()
        return self._ctx

    @property
    def smgr(self):
        return self.ctx.ServiceManager

    @property
    def desktop(self):
        return self.smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx
        )

    def list_documents(self):
        """Return [(index, doc, url, service_name), ...] for open documents."""
        docs = []
        enum = self.desktop.Components.createEnumeration()
        idx = 0
        while enum.hasMoreElements():
            comp = enum.nextElement()
            if hasattr(comp, "getURL"):
                docs.append(
                    (idx, comp, comp.getURL(), _doc_kind(comp))
                )
                idx += 1
        return docs

    def get_document(self, index: int):
        for i, doc, _, _ in self.list_documents():
            if i == index:
                return doc
        raise IndexError(f"no open document with index {index}")

    def create_document(self, kind: str = "writer", hidden: bool = False):
        url = {
            "writer": "private:factory/swriter",
            "calc": "private:factory/scalc",
            "impress": "private:factory/simpress",
            "draw": "private:factory/sdraw",
            "base": "private:factory/sbase",
            "math": "private:factory/smath",
        }.get(kind, kind)
        props = [_prop("Hidden", True)] if hidden else []
        return self.desktop.loadComponentFromURL(url, "_blank", 0, props)

    def open_document(self, path: str, hidden: bool = False):
        url = uno.systemPathToFileUrl(os.path.abspath(path))
        props = [_prop("Hidden", True)] if hidden else []
        return self.desktop.loadComponentFromURL(url, "_blank", 0, props)


def _doc_kind(doc) -> str:
    for svc, name in (
        ("com.sun.star.text.TextDocument", "writer"),
        ("com.sun.star.sheet.SpreadsheetDocument", "calc"),
        ("com.sun.star.presentation.PresentationDocument", "impress"),
        ("com.sun.star.drawing.DrawingDocument", "draw"),
        ("com.sun.star.sdb.OfficeDatabaseDocument", "base"),
        ("com.sun.star.formula.FormulaProperties", "math"),
    ):
        if doc.supportsService(svc):
            return name
    return "unknown"


FILTER_MAP = {
    "writer": {
        "pdf": "writer_pdf_Export",
        "docx": "MS Word 2007 XML",
        "odt": "writer8",
        "txt": "Text (encoded):UTF8",
        "html": "HTML (StarWriter)",
    },
    "calc": {
        "pdf": "calc_pdf_Export",
        "xlsx": "Calc MS Excel 2007 XML",
        "ods": "calc8",
        "csv": "Text - txt - csv (StarCalc):44,34,76",
    },
    "impress": {
        "pdf": "impress_pdf_Export",
        "pptx": "Impress MS PowerPoint 2007 XML",
        "odp": "impress8",
    },
    "draw": {
        "pdf": "draw_pdf_Export",
        "svg": "draw_svg_Export",
        "png": "draw_png_Export",
    },
}
