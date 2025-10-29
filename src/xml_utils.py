from typing import List
from xml.etree.ElementTree import Element, tostring
from xml.sax.saxutils import escape, quoteattr

# Assumed to exist in your codebase:
# - sanitize_tag(tag: str) -> str
# - node_to_etree(node: "FieldNode") -> Element

def _render_element_lines(
    el: Element,
    depth: int,
    indent: int,
    gap_between_siblings: bool
) -> list[str]:
    pad = " " * (depth * indent)
    lines: list[str] = []

    # Open tag with attributes
    open_tag_parts = [f"{pad}<{el.tag}"]
    if el.attrib:
        # Preserve insertion order of attributes (Py3.7+)
        for k, v in el.attrib.items():
            open_tag_parts.append(f" {k}={quoteattr(str(v))}")
    open_tag_parts.append(">")
    lines.append("".join(open_tag_parts))

    # Text content (preserve newlines; indent each line)
    if el.text is not None:
        text = el.text.replace("\r\n", "\n").replace("\r", "\n")
        tpad = " " * ((depth + 1) * indent)
        # Do not strip; preserve blank lines in content
        for tline in text.split("\n"):
            if tline == "":
                lines.append(tpad)  # preserve blank line inside content
            else:
                lines.append(f"{tpad}{escape(tline)}")

    # Children
    children = list(el)
    for i, child in enumerate(children):
        lines.extend(_render_element_lines(child, depth + 1, indent, gap_between_siblings))
        if gap_between_siblings and i < len(children) - 1:
            lines.append("")  # blank line between siblings of the same depth

    # Close tag
    lines.append(f"{pad}</{el.tag}>")

    # Note: We intentionally ignore el.tail to keep output predictable.
    return lines


# def _pretty_print_fragment(
#     root: Element,
#     indent: int = 4,
#     gap_between_siblings: bool = True,
#     trailing_newline: bool = True,
# ) -> str:
#     # Print only the children of the artificial root
#     children = list(root)
#     out_lines: list[str] = []
#     for i, child in enumerate(children):
#         out_lines.extend(_render_element_lines(child, 0, indent, gap_between_siblings))
#         if gap_between_siblings and i < len(children) - 1:
#             out_lines.append("")  # blank line between top-level siblings

#     result = "\n".join(out_lines)
#     if trailing_newline:
#         result += "\n"
#     return result
def _render_element_lines(
    el: Element,
    depth: int,
    indent: int,
    gap_between_siblings: bool
) -> list[str]:
    pad = " " * (depth * indent)
    lines: list[str] = []

    # Open tag with newline before
    open_tag_parts = [f"<{el.tag}"]
    if el.attrib:
        for k, v in el.attrib.items():
            open_tag_parts.append(f" {k}={quoteattr(str(v))}")
    open_tag_parts.append(">")
    lines.append(f"{pad}{''.join(open_tag_parts)}")
    lines.append("")

    # Text content
    if el.text is not None:
        text = el.text.replace("\r\n", "\n").replace("\r", "\n")
        tpad = " " * ((depth + 1) * indent)
        for tline in text.split("\n"):
            lines.append(f"{tpad}{escape(tline)}" if tline else tpad)

    # Children
    children = list(el)
    for child in children:
        lines.extend(_render_element_lines(child, depth + 1, indent, gap_between_siblings))

    # Close tag
    lines.append("")
    lines.append(f"{pad}</{el.tag}>")
    lines.append("")

    return lines
def _pretty_print_fragment(
    root: Element,
    indent: int = 4,
    gap_between_siblings: bool = True,
    trailing_newline: bool = True,
) -> str:
    # Print only the children of the artificial root
    children = list(root)
    out_lines: list[str] = []
    for i, child in enumerate(children):
        out_lines.extend(_render_element_lines(child, 0, indent, gap_between_siblings))
        if gap_between_siblings and i < len(children) - 1:
            out_lines.append("")  # blank line between top-level siblings

    # filter out repeating empty strings
    def _line_check(line):
        return len(line.strip()) == 0
    
    i = 1
    while i < len(out_lines):
        if _line_check(out_lines[i-1]) and _line_check(out_lines[i]):
            out_lines.pop(i)
        else:
            i += 1

    result = "\n".join(out_lines)
    # Remove leading newline if present
    if result.startswith("\n"):
        result = result[1:]
    # Ensure trailing newline
    if trailing_newline and not result.endswith("\n"):
        result += "\n"
    return result

def _to_xml_string(
    root, 
    pretty: bool = True,
    indent: int = 4,
    gap_between_siblings: bool = True,
    drop_root: bool = True,  # True = produce fragment (your target format)
) -> str:
    """
    Serialize a list of FieldNodes into your custom 'prompt XML' format.

    - pretty=True uses a custom pretty-printer (not minidom).
    - indent controls spaces per depth (default: 4).
    - gap_between_siblings inserts a blank line between sibling elements at the same depth.
    - drop_root=True outputs an XML fragment without the outermost root element.
    """
    if not pretty:
        # Compact, root kept or dropped depending on drop_root
        if drop_root:
            return "".join(
                tostring(child, encoding="unicode", short_empty_elements=False)
                for child in list(root)
            )
        else:
            return tostring(root, encoding="unicode", short_empty_elements=False)

    # Pretty path: custom renderer
    if drop_root:
        return _pretty_print_fragment(root, indent=indent, gap_between_siblings=gap_between_siblings)
    else:
        # Keep the outer wrapper but still use our printer
        # (Wrap in a synthetic parent to reuse the fragment printer)
        synthetic = Element("_synthetic_root_")
        synthetic.append(root)
        s = _pretty_print_fragment(synthetic, indent=indent, gap_between_siblings=gap_between_siblings)
        # Strip the synthetic wrapper (first and last line belong to <_synthetic_root_>...</_synthetic_root_>)
        return s
