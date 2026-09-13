#!/usr/bin/env python3
"""
Parse the AltaCV LaTeX source of the CV into structured JSON for the website.

The LaTeX file stays the single source of truth. This script understands the
AltaCV macros used in it (\\cvsection, \\cvsubsection, \\cvevent, \\divider,
itemize lists, \\fullcite with the accompanying .bib file, \\href, \\textbf, ...)
and converts them to a small JSON document that the Jekyll page renders.

Usage:
    python3 cv/build_cv.py                      # JSON to stdout
    python3 cv/build_cv.py --tex cv/mmayer.tex  # explicit source
    python3 cv/build_cv.py --out _data/cv.json  # write to a file

Only the Python standard library is used, so it runs unchanged in CI.
"""

import argparse
import html
import json
import os
import re
import sys
import unicodedata

# --------------------------------------------------------------------------- #
# Low-level LaTeX helpers
# --------------------------------------------------------------------------- #


def strip_comments(src):
    """Remove % comments (but keep escaped \\%)."""
    out = []
    for line in src.split("\n"):
        i = 0
        buf = []
        while i < len(line):
            c = line[i]
            if c == "\\" and i + 1 < len(line):
                buf.append(line[i : i + 2])
                i += 2
                continue
            if c == "%":
                break
            buf.append(c)
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def match_brace(s, i):
    """Given s[i] == '{', return index of the matching '}'."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ValueError("Unbalanced braces near: " + s[i : i + 60])


def read_group(s, i):
    """Skip whitespace, read a {...} group starting at i. Returns (content, next_index).
    If no group follows, returns (None, i)."""
    j = i
    while j < len(s) and s[j] in " \t\n":
        j += 1
    if j < len(s) and s[j] == "{":
        k = match_brace(s, j)
        return s[j + 1 : k], k + 1
    return None, i


def skip_optional(s, i):
    """Skip an optional [...] argument if present."""
    j = i
    while j < len(s) and s[j] in " \t\n":
        j += 1
    if j < len(s) and s[j] == "[":
        depth = 0
        while j < len(s):
            if s[j] == "[":
                depth += 1
            elif s[j] == "]":
                depth -= 1
                if depth == 0:
                    return j + 1
            j += 1
    return i


def find_env_end(s, name, start):
    """Find the index of the matching \\end{name} for an environment whose body starts at `start`."""
    begin_re = re.compile(r"\\begin\{" + re.escape(name) + r"\}")
    end_re = re.compile(r"\\end\{" + re.escape(name) + r"\}")
    depth = 1
    pos = start
    while True:
        mb = begin_re.search(s, pos)
        me = end_re.search(s, pos)
        if me is None:
            raise ValueError(f"Missing \\end{{{name}}}")
        if mb is not None and mb.start() < me.start():
            depth += 1
            pos = mb.end()
        else:
            depth -= 1
            if depth == 0:
                return me.start(), me.end()
            pos = me.end()


ACCENTS = {
    '"': "\u0308",  # diaeresis
    "'": "\u0301",  # acute
    "`": "\u0300",  # grave
    "^": "\u0302",  # circumflex
    "~": "\u0303",  # tilde
    "=": "\u0304",  # macron
    ".": "\u0307",  # dot above
    "u": "\u0306",  # breve
    "v": "\u030c",  # caron
    "H": "\u030b",  # double acute
    "c": "\u0327",  # cedilla
    "k": "\u0328",  # ogonek
    "r": "\u030a",  # ring
}

SYMBOLS = {
    "textdagger": "†",
    "textddagger": "‡",
    "ldots": "…",
    "dots": "…",
    "textbullet": "•",
    "textendash": "–",
    "textemdash": "—",
    "textbackslash": "\\",
    "ss": "ß",
    "o": "ø",
    "O": "Ø",
    "l": "ł",
    "L": "Ł",
    "ae": "æ",
    "AE": "Æ",
    "oe": "œ",
    "OE": "Œ",
    "aa": "å",
    "AA": "Å",
    "i": "ı",
    "textquoteright": "’",
    "textquoteleft": "‘",
    "and": "&amp;",
}

# Commands that only affect layout in LaTeX and produce nothing in HTML.
IGNORED_NO_ARG = {
    "footnotesize", "scriptsize", "tiny", "small", "normalsize", "large", "Large", "LARGE", "huge", "Huge",
    "noindent", "smallskip", "medskip", "bigskip", "par", "hfill", "vfill", "centering", "raggedright",
    "RaggedRight", "raggedleft", "itshape", "bfseries", "normalfont", "relax", "newline", "linebreak",
    "pagebreak", "newpage", "clearpage", "makecvheader", "divider", "nopagebreak", "sloppy",
}
# Commands whose arguments are consumed and dropped (name -> number of brace args).
IGNORED_WITH_ARGS = {
    "vspace": 1, "hspace": 1, "setlength": 2, "addtolength": 2, "setcounter": 2, "defcounter": 2,
    "label": 1, "phantom": 1, "hphantom": 1, "vphantom": 1, "columnbreak": 0, "cvskill": 2,
    "cvtag": 1, "photo": 2, "colorlet": 2, "definecolor": 3, "color": 1, "textcolor": 2,
}
BOLD_CMDS = {"textbf"}
ITALIC_CMDS = {"emph", "textit", "textsl"}
INLINE_CMDS = {
    "textsc": ("<span style=\"font-variant: small-caps\">", "</span>"),
    "texttt": ("<code>", "</code>"),
    "underline": ("<u>", "</u>"),
    "textsuperscript": ("<sup>", "</sup>"),
    "textsubscript": ("<sub>", "</sub>"),
    "mbox": ("", ""),
    "text": ("", ""),
    "textnormal": ("", ""),
    "textrm": ("", ""),
    "textup": ("", ""),
    "textmd": ("", ""),
    "MakeUppercase": ("", ""),
}


class Converter:
    """Converts inline LaTeX to HTML. `cite` resolves \\fullcite keys to HTML."""

    def __init__(self, cite=None):
        self.cite = cite or (lambda key: f"<em>[{html.escape(key)}]</em>")
        self.warnings = []
        self.flags = set()

    def convert(self, s):
        out = []
        i = 0
        n = len(s)
        while i < n:
            c = s[i]
            if c == "\\":
                i = self._command(s, i, out)
            elif c == "{":
                k = match_brace(s, i)
                out.append(self.convert(s[i + 1 : k]))
                i = k + 1
            elif c == "}":
                i += 1
            elif c == "~":
                out.append("&nbsp;")
                i += 1
            elif c == "-" and s.startswith("---", i):
                out.append("—")
                i += 3
            elif c == "-" and s.startswith("--", i):
                out.append("–")
                i += 2
            elif c == "`" and s.startswith("``", i):
                out.append("“")
                i += 2
            elif c == "'" and s.startswith("''", i):
                out.append("”")
                i += 2
            elif c == "`":
                out.append("‘")
                i += 1
            elif c == "$":
                j = s.find("$", i + 1)
                if j == -1:
                    j = n
                out.append(html.escape(s[i + 1 : j]))
                i = j + 1
            else:
                out.append(html.escape(c))
                i += 1
        return "".join(out)

    def _command(self, s, i, out):
        n = len(s)
        m = re.match(r"\\([A-Za-z]+)\*?", s[i:])
        if not m:
            nxt = s[i + 1] if i + 1 < n else ""
            if nxt in ACCENTS and nxt not in "ucvHkr":
                return self._accent(s, i + 2, nxt, out)
            if nxt == "\\":
                out.append("<br>")
                return i + 2
            if nxt in "&%$#_{}":
                out.append(html.escape(nxt))
                return i + 2
            if nxt == ",":
                out.append("&thinsp;")
                return i + 2
            if nxt in " \n":
                out.append(" ")
                return i + 2
            if nxt in "-/":
                return i + 2
            out.append(html.escape(nxt))
            return i + 2

        name = m.group(1)
        j = i + m.end()
        # TeX swallows whitespace after a control word
        while j < n and s[j] in " \t\n":
            j += 1

        if name in ("footnotesize", "scriptsize", "small", "tiny"):
            self.flags.add("small")
        if name in IGNORED_NO_ARG:
            return j
        if name in IGNORED_WITH_ARGS:
            nargs = IGNORED_WITH_ARGS[name]
            j = skip_optional(s, j)
            for _ in range(nargs):
                # e.g. \setlength\itemsep{0em}: first "arg" may be a control word
                if j < n and s[j] == "\\":
                    m2 = re.match(r"\\[A-Za-z]+", s[j:])
                    j += m2.end() if m2 else 1
                    continue
                _, j = read_group(s, j)
            return j
        if name in SYMBOLS:
            out.append(SYMBOLS[name])
            return j
        if name in ACCENTS:  # letter accents such as \c{c}, \v{s}
            arg, j2 = read_group(s, j)
            if arg is None:
                arg = s[j] if j < n else ""
                j2 = j + 1
            base = self.convert(arg)
            out.append(unicodedata.normalize("NFC", base + ACCENTS[name]))
            return j2
        if name in BOLD_CMDS:
            arg, j = read_group(s, j)
            out.append("<strong>" + self.convert(arg or "") + "</strong>")
            return j
        if name in ITALIC_CMDS:
            arg, j = read_group(s, j)
            out.append("<em>" + self.convert(arg or "") + "</em>")
            return j
        if name in INLINE_CMDS:
            open_tag, close_tag = INLINE_CMDS[name]
            arg, j = read_group(s, j)
            out.append(open_tag + self.convert(arg or "") + close_tag)
            return j
        if name == "href":
            url, j = read_group(s, j)
            text, j = read_group(s, j)
            url = (url or "").strip()
            if url.startswith("tps://"):
                url = "ht" + url
            if url and not re.match(r"^[a-z]+:", url):
                url = "https://" + url
            out.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{self.convert(text or "")}</a>')
            return j
        if name == "url":
            url, j = read_group(s, j)
            url = (url or "").strip()
            out.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(url)}</a>')
            return j
        if name in ("fullcite", "cite", "citep", "citet", "textcite", "parencite"):
            j = skip_optional(s, j)
            key, j = read_group(s, j)
            out.append(self.cite((key or "").strip()))
            return j
        if name.startswith("fa") and name[2:3].isupper():
            return j  # FontAwesome icon macros
        # Unknown command: keep its argument's text, if any, otherwise drop it.
        arg, j2 = read_group(s, j)
        if arg is not None:
            self.warnings.append(f"unknown command \\{name}: kept its argument")
            out.append(self.convert(arg))
            return j2
        self.warnings.append(f"unknown command \\{name}: dropped")
        return j

    def _accent(self, s, i, kind, out):
        arg, j = read_group(s, i)
        if arg is None:
            arg = s[i] if i < len(s) else ""
            j = i + 1
        base = self.convert(arg)
        out.append(unicodedata.normalize("NFC", base + ACCENTS[kind]))
        return j


def tidy(h):
    """Collapse whitespace in generated HTML."""
    h = re.sub(r"[ \t]*\n[ \t]*", " ", h)
    h = re.sub(r"\s{2,}", " ", h)
    h = re.sub(r"\s+(<br>)\s*", r"\1", h)
    return h.strip()


# --------------------------------------------------------------------------- #
# BibTeX parsing and APA-like formatting
# --------------------------------------------------------------------------- #


def parse_bib(src):
    entries = {}
    src = strip_comments(src)
    for m in re.finditer(r"@(\w+)\s*\{", src):
        etype = m.group(1).lower()
        if etype in ("comment", "preamble", "string"):
            continue
        start = m.end() - 1
        end = match_brace(src, start)
        body = src[start + 1 : end]
        key, _, rest = body.partition(",")
        key = key.strip()
        fields = {}
        i = 0
        while i < len(rest):
            fm = re.match(r"\s*([\w\-]+)\s*=\s*", rest[i:])
            if not fm:
                break
            fname = fm.group(1).lower()
            i += fm.end()
            if i < len(rest) and rest[i] == "{":
                k = match_brace(rest, i)
                val = rest[i + 1 : k]
                i = k + 1
            elif i < len(rest) and rest[i] == '"':
                k = rest.find('"', i + 1)
                val = rest[i + 1 : k]
                i = k + 1
            else:
                vm = re.match(r"[^,]*", rest[i:])
                val = vm.group(0)
                i += vm.end()
            fields[fname] = val.strip()
            cm = re.match(r"\s*,", rest[i:])
            if cm:
                i += cm.end()
        entries[key] = {"type": etype, "key": key, **fields}
    return entries


def split_top_level(s, sep=" and "):
    parts = []
    depth = 0
    cur = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            parts.append("".join(cur))
            cur = []
            i += len(sep)
            continue
        cur.append(c)
        i += 1
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def strip_outer_braces(s):
    s = s.strip()
    while s.startswith("{") and match_brace(s, 0) == len(s) - 1:
        s = s[1:-1].strip()
    return s


def format_author(raw, conv):
    """Return HTML for one author as 'Last, F. M.', preserving bold and dagger marks."""
    a = raw.strip()
    marks = ""
    sup = re.search(r"\\textsuperscript\{([^}]*)\}", a)
    if sup:
        marks = "<sup>" + conv.convert(sup.group(1)) + "</sup>"
        a = a.replace(sup.group(0), "")
    bold = False
    while True:  # unwrap \textbf{...} wherever it appears; the whole name is rendered bold
        m = re.search(r"\\textbf\{", a)
        if not m:
            break
        k = match_brace(a, m.end() - 1)
        a = a[: m.start()] + a[m.end() : k] + a[k + 1 :]
        bold = True
    a = strip_outer_braces(a).strip()
    if "," in a:
        last, first = [p.strip() for p in a.split(",", 1)]
    else:
        parts = a.split()
        last = parts[-1] if parts else a
        first = " ".join(parts[:-1])
    tokens = [t for t in re.split(r"[\s\-]+", first) if t]
    initials = []
    for t in tokens:
        plain = re.sub(r"\\[A-Za-z]+|[{}]", "", t)
        if re.fullmatch(r"(?:[A-Za-z]\.)+", plain):  # already initials like P.M.
            initials.append(plain)
        elif plain:
            initials.append(plain[0].upper() + ".")
    name = conv.convert(last)
    if initials:
        name += ", " + " ".join(initials)
    if bold:
        name = "<strong>" + name + "</strong>"
    return name + marks


def format_entry(e, conv):
    """APA-ish rendering of a bib entry (mirrors biblatex-apa closely enough for a CV)."""
    authors = [format_author(a, conv) for a in split_top_level(e.get("author", ""))]
    if len(authors) > 2:
        auth = ", ".join(authors[:-1]) + ", &amp; " + authors[-1]
    elif len(authors) == 2:
        auth = authors[0] + " &amp; " + authors[1]
    else:
        auth = authors[0] if authors else ""
    year = conv.convert(strip_outer_braces(e.get("year", "n.d.")))
    title = conv.convert(strip_outer_braces(e.get("title", "")))
    t = e["type"]
    venue = ""
    if t == "article":
        venue = "<em>" + conv.convert(strip_outer_braces(e.get("journal", ""))) + "</em>"
        if e.get("volume"):
            venue += ", <em>" + conv.convert(e["volume"]) + "</em>"
            if e.get("number"):
                venue += "(" + conv.convert(e["number"]) + ")"
    elif t in ("inproceedings", "conference", "incollection"):
        venue = "<em>" + conv.convert(strip_outer_braces(e.get("booktitle", ""))) + "</em>"
        if e.get("volume"):
            venue += ", <em>" + conv.convert(e["volume"]) + "</em>"
            if e.get("number"):
                venue += "(" + conv.convert(e["number"]) + ")"
    elif t in ("phdthesis", "mastersthesis"):
        kind = e.get("type", "PhD thesis" if t == "phdthesis" else "Master's thesis")
        venue = "[" + conv.convert(kind) + ", " + conv.convert(e.get("school", "")) + "]"
    elif t in ("misc", "unpublished", "online"):
        bits = []
        if e.get("note"):
            bits.append("[" + conv.convert(e["note"]) + "]")
        if e.get("publisher"):
            bits.append(conv.convert(e["publisher"]))
        venue = " ".join(bits)
    else:
        venue = conv.convert(e.get("journal") or e.get("booktitle") or e.get("publisher") or "")
    parts = [f"{auth} ({year}).", title + ("" if title.endswith((".", "?", "!")) else ".")]
    if venue:
        parts.append(venue.rstrip(".") + ".")
    if e.get("doi"):
        doi = e["doi"].strip()
        url = doi if doi.startswith("http") else "https://doi.org/" + doi
        parts.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(url)}</a>')
    elif e.get("url"):
        parts.append(f'<a href="{html.escape(e["url"], quote=True)}" target="_blank" rel="noopener">{html.escape(e["url"])}</a>')
    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Document structure
# --------------------------------------------------------------------------- #

CONTACT_ICONS = {
    "location": "fa-solid fa-location-dot",
    "mailaddress": "fa-solid fa-envelope",
    "email": "fa-solid fa-at",
    "phone": "fa-solid fa-phone",
    "homepage": "fa-solid fa-globe",
    "linkedin": "fa-brands fa-linkedin",
    "github": "fa-brands fa-github",
    "twitter": "fa-brands fa-x-twitter",
    "scholar": "ai ai-google-scholar",
    "orcid": "ai ai-orcid",
    "printinfo": "",
}


def parse_personalinfo(s, conv):
    items = []
    i = 0
    while i < len(s):
        m = re.compile(r"\\([A-Za-z]+)").search(s, i)
        if not m:
            break
        name = m.group(1)
        if name in CONTACT_ICONS:
            j = m.end()
            if name == "printinfo":
                icon, j = read_group(s, j)
                icon = ""
            else:
                icon = CONTACT_ICONS[name]
            text, j = read_group(s, j)
            items.append({"kind": name, "icon": icon, "html": tidy(conv.convert(text or ""))})
            i = j
        else:
            i = m.end()
    return items


def parse_items(body, conv):
    """Parse the body of an itemize environment into a list of {html, children}."""
    items = []
    # split on \item at depth 0 (outside nested environments)
    pieces = []
    depth = 0
    pos = 0
    i = 0
    while i < len(body):
        if body.startswith("\\begin{", i):
            depth += 1
        elif body.startswith("\\end{", i):
            depth -= 1
        elif depth == 0 and body.startswith("\\item", i) and not body[i + 5 : i + 6].isalpha():
            pieces.append(body[pos:i])
            pos = i + 5
            i = pos
            continue
        i += 1
    pieces.append(body[pos:])
    for piece in pieces[1:]:  # pieces[0] is whatever precedes the first \item (e.g. \setlength)
        text = piece
        children = []
        # extract nested itemize environments
        while True:
            mb = re.search(r"\\begin\{(itemize|enumerate)\}", text)
            if not mb:
                break
            env = mb.group(1)
            end_start, end_end = find_env_end(text, env, mb.end())
            children.extend(parse_items(text[mb.end() : end_start], conv))
            text = text[: mb.start()] + text[end_end:]
        conv.flags.clear()
        h = tidy(conv.convert(text))
        if h or children:
            item = {"html": h}
            if children:
                item["children"] = children
            items.append(item)
    return items


BLOCK_RE = re.compile(
    r"\\(cvsection|cvsubsection|cvevent|cvproject|divider|smallskip|medskip|bigskip|pagebreak|newpage|clearpage)\b"
    r"|\\begin\{(itemize|enumerate|flushright|flushleft|center)\}"
    r"|\\begin\{[A-Za-z*]+\}|\\end\{[A-Za-z*]+\}"
)


def parse_body(body, conv):
    sections = []
    current = None
    text_buf = []

    def flush_text(align=None):
        raw = "".join(text_buf)
        text_buf.clear()
        conv.flags.clear()
        h = tidy(conv.convert(raw))
        if not h:
            return
        block = {"type": "text", "html": h}
        if "small" in conv.flags:
            block["small"] = True
        if align:
            block["align"] = align
        blocks().append(block)

    def blocks():
        nonlocal current
        if current is None:
            current = {"title": "", "blocks": []}
            sections.append(current)
        return current["blocks"]

    i = 0
    n = len(body)
    while i < n:
        m = BLOCK_RE.search(body, i)
        if not m:
            text_buf.append(body[i:])
            break
        text_buf.append(body[i : m.start()])
        tok = m.group(0)
        name = m.group(1)
        env = m.group(2)
        j = m.end()
        if name == "cvsection":
            flush_text()
            title, j = read_group(body, skip_optional(body, j))
            current = {"title": tidy(conv.convert(title or "")), "blocks": []}
            sections.append(current)
        elif name == "cvsubsection":
            flush_text()
            title, j = read_group(body, j)
            blocks().append({"type": "subsection", "title": tidy(conv.convert(title or ""))})
        elif name in ("cvevent", "cvproject"):
            flush_text()
            args = []
            for _ in range(4 if name == "cvevent" else 2):
                a, j = read_group(body, j)
                args.append(tidy(conv.convert(a or "")))
            ev = {"type": "event", "title": args[0], "org": args[1]}
            if name == "cvevent":
                ev["dates"] = args[2]
                ev["location"] = args[3]
            blocks().append(ev)
        elif name == "divider":
            flush_text()
            blocks().append({"type": "divider"})
        elif name in ("smallskip", "medskip", "bigskip", "pagebreak", "newpage", "clearpage"):
            pass
        elif env in ("itemize", "enumerate"):
            flush_text()
            end_start, end_end = find_env_end(body, env, j)
            items = parse_items(body[j:end_start], conv)
            bl = blocks()
            if bl and bl[-1]["type"] == "event" and "items" not in bl[-1]:
                bl[-1]["items"] = items
            else:
                bl.append({"type": "items", "items": items, "ordered": env == "enumerate"})
            j = end_end
        elif env in ("flushright", "flushleft", "center"):
            flush_text()
            end_start, end_end = find_env_end(body, env, j)
            text_buf.append(body[j:end_start])
            flush_text(align={"flushright": "right", "flushleft": "left", "center": "center"}[env])
            j = end_end
        else:
            # any other \begin{...}/\end{...}: drop the wrapper, keep parsing its contents inline
            if tok.startswith("\\begin"):
                j = skip_optional(body, j)
                # consume a mandatory width-like argument for minipage/multicols
                if re.match(r"\\begin\{(minipage|multicols|wrapfigure)\}", tok):
                    _, j = read_group(body, j)
        i = j
    flush_text()
    return sections


def build(tex_path):
    with open(tex_path, encoding="utf-8") as f:
        src = strip_comments(f.read())

    # bibliography
    entries = {}
    bibs = re.findall(r"\\addbibresource(?:\[[^\]]*\])?\{([^}]*)\}", src) + re.findall(r"\\bibliography\{([^}]*)\}", src)
    for b in bibs:
        for name in b.split(","):
            name = name.strip()
            if not name.endswith(".bib"):
                name += ".bib"
            p = os.path.join(os.path.dirname(tex_path), name)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    entries.update(parse_bib(f.read()))
            else:
                print(f"warning: bib file not found: {p}", file=sys.stderr)

    conv = Converter()

    def cite(key):
        e = entries.get(key)
        if not e:
            conv.warnings.append(f"unknown citation key {key}")
            return f"<em>[{html.escape(key)}]</em>"
        return format_entry(e, conv)

    conv.cite = cite

    mdoc = re.search(r"\\begin\{document\}(.*)\\end\{document\}", src, re.S)
    body = mdoc.group(1) if mdoc else src

    name_m = re.search(r"\\name\{", body)
    name = ""
    if name_m:
        k = match_brace(body, name_m.end() - 1)
        name = tidy(conv.convert(body[name_m.end() : k]))
        body = body[: name_m.start()] + body[k + 1 :]
    tag_m = re.search(r"\\tagline\{", body)
    tagline = ""
    if tag_m:
        k = match_brace(body, tag_m.end() - 1)
        tagline = tidy(conv.convert(body[tag_m.end() : k]))
        body = body[: tag_m.start()] + body[k + 1 :]
    contact = []
    pi_m = re.search(r"\\personalinfo\{", body)
    if pi_m:
        k = match_brace(body, pi_m.end() - 1)
        contact = parse_personalinfo(body[pi_m.end() : k], conv)
        body = body[: pi_m.start()] + body[k + 1 :]

    sections = parse_body(body, conv)
    sections = [s for s in sections if s["title"] or s["blocks"]]

    for w in sorted(set(conv.warnings)):
        print("warning: " + w, file=sys.stderr)

    return {
        "source": os.path.relpath(tex_path),
        "name": name,
        "tagline": tagline,
        "contact": contact,
        "sections": sections,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tex", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mmayer.tex"))
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args()
    data = build(args.tex)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
