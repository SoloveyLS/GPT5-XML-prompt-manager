## GPT-5 XML prompt manager

The OpenAI cookbook says that GPT-5-High works better with prompts formatted with XML tags—so I built this little tool to speed up XML tag construction for lazy folks like me.

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
uv run pyinstaller --onefile --add-data "templates:templates" --add-data "static:static" app.py
```
or without `uv`:
```
pyinstaller --onefile --add-data "templates:templates" --add-data "static:static" app.py
```
