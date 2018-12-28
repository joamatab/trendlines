# -*- coding: utf-8 -*-
from flask import Flask
from flask import g

from trendlines import routes
from trendlines import orm

def create_app():
    """
    Primary application factory.
    """

    app = Flask(__name__)

    app.register_blueprint(routes.pages)
    app.register_blueprint(routes.api)

    # Create the database file and populate initial tables if needed.
    create_db()

    # If I redesign the architecture a bit, then these could be moved so
    # that they only act on the `api` blueprint instead of the entire app.
    #
    # Also, note that this is safe for multiple simultaneous requests, since
    # the database object is thread local:
    #   "Peewee uses thread local storage to manage connection state, so
    #    this pattern can be used with multi-threaded WSGI servers."
    # http://docs.peewee-orm.com/en/latest/peewee/example.html#establishing-a-database-connection
    @app.before_request
    def before_request():
        """
        Attach the ORM to the flask ``g`` object before every request.

        Why not just use ``from orm import db`` most of the time? Well, it's
        because:
        (a) that's how I'm used to from SQLAlchemy
        (b) I may need ``db`` somewhere where I *can't* import ``orm``
        (c) because that's how the example PeeWee project is set up. /shrug.
            https://github.com/coleifer/peewee/blob/master/examples/twitter/app.py#L152
        """
        g.db = orm.db
        g.db.connect()

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

    return app


def create_db():
    """
    Create the database and the tables.

    Does nothing if the tables already exist. Well, techinically it just
    connects and disconnects - ``create_tables`` is a noop.
    """
    orm.db.connect()
    tables = [
        orm.Metric,
        orm.DataPoint,
    ]
    orm.db.create_tables(tables)
    orm.db.close()
