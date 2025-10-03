from __future__ import annotations
import uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, make_response

DEV = True

def resource_path(path):
    import os, sys
    global DEV
    if hasattr(sys, "_MEIPASS"):  # Only exists inside PyInstaller binary
        DEV = False
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)

from models import (
    FieldNode,
    generate_default_tree,
    find_by_id,
    find_parent_and_index,
    to_xml_string,
    sanitize_tag,
)
from store import load_state, save_state


# Load or initialize state
fields = load_state()
if fields is None:
    fields = generate_default_tree()
    save_state(fields)


def anchor_redirect(field_id: str | None = None):
    url = url_for("index")
    if field_id:
        url = f"{url}#f-{field_id}"
    # 303 to force GET after POST
    resp = redirect(url, code=303)
    return resp


@app.route("/")
def index():
    return render_template("index.html", fields=fields)


@app.route("/add", methods=["POST"])
def add_field():
    parent_id = request.form.get("parent_id")  # None or field id
    tag_raw = request.form.get("tag", "") or "new_field"
    tag = sanitize_tag(tag_raw)
    new = FieldNode(id=str(uuid.uuid4()), tag=tag, text="", children=[])

    if parent_id:
        parent = find_by_id(fields, parent_id)
        if not parent:
            return anchor_redirect()
        parent.children.append(new)
    else:
        fields.append(new)

    save_state(fields)
    return anchor_redirect(new.id)


@app.route("/update", methods=["POST"])
def update_field():
    fid = request.form.get("id")
    if not fid:
        return anchor_redirect()

    node = find_by_id(fields, fid)
    if not node:
        return anchor_redirect()

    tag_raw = request.form.get("tag")
    text = request.form.get("text")

    if tag_raw is not None:
        node.tag = sanitize_tag(tag_raw)

    if text is not None:
        node.text = text

    save_state(fields)

    # If this is an autosave (AJAX/fetch) request, don't redirect
    if request.headers.get("X-Autosave") == "1":
        return ("", 204)

    return anchor_redirect(fid)


@app.route("/move", methods=["POST"])
def move_field():
    fid = request.form.get("id")
    direction = request.form.get("direction")  # "up" or "down"
    if not fid or direction not in ("up", "down"):
        return anchor_redirect()

    siblings, idx = find_parent_and_index(fields, fid)
    if siblings is None or idx is None:
        return anchor_redirect()

    if direction == "up" and idx > 0:
        siblings[idx - 1], siblings[idx] = siblings[idx], siblings[idx - 1]
    elif direction == "down" and idx < len(siblings) - 1:
        siblings[idx + 1], siblings[idx] = siblings[idx], siblings[idx + 1]

    save_state(fields)
    return anchor_redirect(fid)


@app.route("/delete", methods=["POST"])
def delete_field():
    fid = request.form.get("id")
    if not fid:
        return anchor_redirect()

    siblings, idx = find_parent_and_index(fields, fid)
    if siblings is None or idx is None:
        return anchor_redirect()

    # remove
    siblings.pop(idx)
    save_state(fields)
    return anchor_redirect()


@app.route("/preview")
def preview_xml():
    # Pretty XML with a single <prompt> root element
    xml_text = to_xml_string(fields, root_tag="prompt", pretty=True)
    return render_template("preview.html", xml_text=xml_text)


@app.route("/download")
def download_xml():
    xml_text = to_xml_string(fields, root_tag="prompt", pretty=True)
    resp = make_response(xml_text)
    resp.headers["Content-Type"] = "application/xml; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=prompt.xml"
    return resp


@app.route("/reset")
def reset():
    global fields
    fields = generate_default_tree()
    save_state(fields)
    return anchor_redirect()


if __name__ == "__main__":
    app.run(debug=not DEV)