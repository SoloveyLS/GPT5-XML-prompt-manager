from __future__ import annotations
from dataclasses import dataclass, field as dcfield
from typing import List, Optional, Tuple
import re
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom

@dataclass
class FieldNode:
    id: str
    tag: str
    text: str = ""
    children: List["FieldNode"] = dcfield(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "tag": self.tag,
            "text": self.text,
            "children": [c.to_dict() for c in self.children],
        }

    @staticmethod
    def from_dict(d: dict) -> "FieldNode":
        return FieldNode(
            id=d["id"],
            tag=d["tag"],
            text=d.get("text", ""),
            children=[FieldNode.from_dict(c) for c in d.get("children", [])],
        )


def sanitize_tag(tag: str) -> str:
    """
    Make a best-effort valid XML tag:
    - Replace spaces with underscores
    - Remove invalid characters
    - Ensure it starts with a letter or underscore
    """
    tag = (tag or "").strip()
    if not tag:
        tag = "field"
    tag = tag.replace(" ", "_")
    # Allow letters, digits, underscore, dash, dot, colon
    tag = re.sub(r"[^A-Za-z0-9_\-.:]", "_", tag)
    # XML tag must not start with digit or punctuation
    if not re.match(r"^[A-Za-z_]", tag):
        tag = f"_{tag}"
    return tag


def generate_default_tree() -> List[FieldNode]:
    import uuid
    context = FieldNode(
        id=str(uuid.uuid4()),
        tag="context",
        text="I'm an AI R&D Engineer that ...",
        children=[],
    )
    task = FieldNode(
        id=str(uuid.uuid4()),
        tag="task",
        text="",
        children=[],
    )
    self_reflection = FieldNode(
        id=str(uuid.uuid4()),
        tag="self_reflection",
        text=(
            "- First, spend time thinking of a rubric until you are confident.\n\n"
            "- Then, think deeply about every aspect of what makes for a world-class one-shot solution. "
            "Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, "
            "but do not show this to the user. This is for your purposes only.\n\n"
            "- Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided. "
            "Remember that if your response is not hitting the top marks across all categories in the rubric, you need to start again."
        ),
        children=[],
    )
    return [context, task, self_reflection]


def find_by_id(nodes: List[FieldNode], fid: str) -> Optional[FieldNode]:
    for n in nodes:
        if n.id == fid:
            return n
        got = find_by_id(n.children, fid)
        if got:
            return got
    return None


def find_parent_and_index(nodes: List[FieldNode], fid: str) -> Tuple[Optional[List[FieldNode]], Optional[int]]:
    for i, n in enumerate(nodes):
        if n.id == fid:
            return nodes, i
        siblings, idx = find_parent_and_index(n.children, fid)
        if siblings is not None:
            return siblings, idx
    return None, None


def node_to_etree(n: FieldNode) -> Element:
    e = Element(n.tag)
    # Preserve text; if empty and has children, keep None to avoid stray whitespace
    if n.text:
        e.text = n.text
    for c in n.children:
        e.append(node_to_etree(c))
    return e


def to_xml_string(nodes: List[FieldNode], root_tag: str = "prompt", pretty: bool = True) -> str:
    root = Element(root_tag)
    for n in nodes:
        # ensure tags are sanitized at serialization time too
        n.tag = sanitize_tag(n.tag)
        root.append(node_to_etree(n))

    from src.xml_utils import _to_xml_string

    return _to_xml_string(
        root, pretty=pretty, 
    )

    raw = tostring(root, encoding="utf-8")
    if not pretty:
        return raw.decode("utf-8")

    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")