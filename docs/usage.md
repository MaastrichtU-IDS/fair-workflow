This page explains how to create a FAIR metrics test API with `fair-workflow`.

## 📥 Install the package

Install the package from [PyPI](https://pypi.org/project/fair-workflow/){:target="_blank"}:

```bash
pip install fair-workflow
```


## 📝 Define the API

Create a `main.py` file to declare the API, you can provide a different folder than `metrics` here, the folder path is relative to where you start the API (the root of the repository):

```python title="main.py"
from fair_workflow import Api

api = API()
print(api.get_hello_world())
```
