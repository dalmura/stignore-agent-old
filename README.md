# stignore-agent
HTTP API Agent for managing Syncthing's .stignore files on this machine

# Development
## Local Setup
```
python3 -m venv venv
source venv/bin/activate

pip3 install --upgrade pip wheel

# Normal install
pip3 install -e '.'

# Including dev dependencies
pip3 install -e '.[dev]'
```

## Linting/Formatting
```
pylint stignore_agent
black -t py39 stignore_agent
```
