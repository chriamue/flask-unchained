import os

from alembic import command as alembic
from flask import current_app
from flask_migrate.cli import db
from flask_unchained import click, unchained

maybe_fixtures_command = db.command
try:
    from py_yaml_fixtures import FixturesLoader
    from py_yaml_fixtures.factories import SQLAlchemyModelFactory
except ImportError:
    # disable the import-fixtures command if py_yaml_fixtures isn't installed
    maybe_fixtures_command = lambda *a, **kw: lambda fn: None

from .extensions import SQLAlchemy, migrate

db_ext: SQLAlchemy = unchained.extensions.db


@db.command('drop')
@click.option('--drop', is_flag=True, expose_value=True,
              prompt='Drop DB tables?')
def drop_command(drop):
    """Drop database tables."""
    if not drop:
        exit('Cancelled.')

    click.echo('Dropping DB tables.')
    drop_all()

    click.echo('Done.')


def drop_all():
    db_ext.drop_all()
    db_ext.engine.execute('DROP TABLE IF EXISTS alembic_version;')


@db.command('reset')
@click.option('--reset', is_flag=True, expose_value=True,
              prompt='Drop DB tables and run migrations?')
def reset_command(reset):
    """Drop database tables and run migrations."""
    if not reset:
        exit('Cancelled.')

    click.echo('Dropping DB tables.')
    drop_all()

    click.echo('Running DB migrations.')
    alembic.upgrade(migrate.get_config(None), 'head')

    click.echo('Done.')


@maybe_fixtures_command(name='import-fixtures')
def import_fixtures():
    fixtures_dir = current_app.config.get('PY_YAML_FIXTURES_DIR')
    if not fixtures_dir or not os.path.exists(fixtures_dir):
        msg = (f'Could not find the {fixtures_dir} directory, please make sure '
               'PY_YAML_FIXTURES_DIR is set correctly and the directory exists')
        raise NotADirectoryError(msg)

    factory = SQLAlchemyModelFactory(db_ext.session,
                                     unchained.sqlalchemy_bundle.store.models)
    loader = FixturesLoader(factory, fixtures_dir=fixtures_dir)

    click.echo(f'Loading fixtures from `{fixtures_dir}` directory')
    for identifier_key, model in loader.create_all().items():
        click.echo(f'Created {identifier_key}: {model!r}')
    click.echo('Finished adding fixtures')
