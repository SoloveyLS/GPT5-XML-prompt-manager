## GPT-5 XML prompt manager

By the OpenAI cookbook it is known that the GPT-5-High works better with prompts that are structured in a same way as the XML file. So this is just a tool for the lazy people like me to prepare those XMLs a bit faster.

## TODO:

- [ ] Shortcuts
- [ ] Template managing

## Usage:

### With `uv`:

```
uv run app.py
```

### With `pip`:

```
cd /path/to/GPT5-XML-prompt-manager
python -m venv .venv
source ./.venv/bin/activate
python app.py
```

### With binary:

```
/path/to/app
```

### Build:

```
uv pyinstaller --onefile --add-data "templates:templates" --add-data "static:static" app.py 
```
or without `uv`:
```
pyinstaller app.py --onefile --add-data "templates:templates" --add-data "static:static"
```
