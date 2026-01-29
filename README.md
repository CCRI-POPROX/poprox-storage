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
alembic revision -m "<what does this migratino do>" --head heads
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

### Create a New Migration File (update the db)

- Make sure installation of all dev dependencies above
- Run `alembic revision -m "<what does this migratino do>" --head heads`
- The command above will create a new migration file under the poprox-db/migratios/versions file; refer to example in poprox-db/migratios/versions file (one example from 2025_11_07) to make upgrade() and downgrade() changes
- If have POPROX local db, can test the changes locally first to verify
- Push the PR for review
