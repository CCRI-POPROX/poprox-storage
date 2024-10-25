# poprox-storage

[![PyPI - Version](https://img.shields.io/pypi/v/poprox-storage.svg)](https://pypi.org/project/poprox-storage)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/poprox-storage.svg)](https://pypi.org/project/poprox-storage)

-----

**Table of Contents**

- [Installation](#installation)


## Installation

```console
pip install poprox-storage
```

### Dev Dependencies

```console
pip install .[dev]
```

### Making Database Schema Changes

We use [alembic](https://alembic.sqlalchemy.org/en/latest/) to manage schema changes as a series of migrations. You can [create a new migration file](https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script) from the `poprox-db` directory with:
```
alembic revision -m "description of your changes"
```

### Running the tests

Start the dev database and load the database schema with:

```console:
source dev/init_poprox_dev.sh
```

Then run the tests with:

```console
pytest tests/
```
