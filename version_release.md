# To release a new version:
- Increment the version number in [`guavacado/version_number.py`](./guavacado/version_number.py)
- Run the following commands:
```sh
python -m pip install --upgrade build
python -m build
python -m pip install --upgrade twine
python -m twine upload dist/*
```