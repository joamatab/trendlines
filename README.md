# Trendlines

A simple, lightweight alternative to [Graphite](https://graphiteapp.org).

[![Build Status](https://travis-ci.org/dougthor42/trendlines.svg?branch=master)](https://travis-ci.org/dougthor42/trendlines)
[![Coverage Status](https://coveralls.io/repos/github/dougthor42/trendlines/badge.svg)](https://coveralls.io/github/dougthor42/trendlines)


## What is Trendlines?

**Trendlines** is a tool for *passively* collecting and displaying time-based
or sequential numeric data. Built on [Flask](http://flask.pocoo.org/),
[PeeWee](http://docs.peewee-orm.com/en/latest/), and
[Plotly](https://plot.ly/), it provides a simple interface for adding and
viewing your metrics.

It was created for a few reasons:

1. [Graphite](https://graphiteapp.org), while very awesome and powerful,
   does not provide a TCP way of sending in data - only UDP. **Trendlines**
   aims to provide both.
2. Graphite also does not allow you to view data using a simple sequential
   x-axis - it only uses time for the x-axis. Again, **Trendlines** allows you
   to use both.
3. It's always fun to start new projects.

**Trendlines** only accepts data that gets sent to it. It does not actively
seek out data like many other monitoring programs out there (Zabbix, Nagios,
Prometheus, etc.).


## What can I use it for?

Anything, really. Well, anything that (a) you can assign a number to and
(b) might change over time.

Examples include:

+ Test coverage per project
+ Code quality metrics per commit
+ House temperature
+ Distance driven per trip
+ Distance per fillup (or per charge for the eco-friendly folk)
+ How many times the dog barks
+ How often some clicks the Big Red Button on your webpage

It's been designed to handle infrequent, variable interval data. Sometimes
real-world data just doesn't appear at nice, regular intervals.


## Installing


### Docker

The easiest way to get up and running with **Trendlines** is with Docker:

```bash
$ docker run p 5000:80 dougthor42/trendlines:latest
```

Then open a browser to `http://localhost:5000/` and you're all set. Add some data
(see below) and refresh the page.

> **Note:** Data will not persist when the container is destroyed!


### Docker Compose

> **WIP!**

If you're doing more than just playing around, you'll likely want to set up
Docker Compose. I've included an example Compose file
[here](/docker/docker-compose.yml).

Before using the example Compose file, you'll need to:

1. Make a directory to store the config file (and database file if using
   SQLite)
2. Make sure that dir is writable by docker-compose.
3. Create the configuration `trendlines.cfg` within that directory.

```bash
$ mkdir /var/www/trendlines
$ chmod -R a+w /var/www/trendlines
$ touch /var/www/trendlines/trendlines.cfg
```

Next, edit your new `trendlines.cfg` file as needed. At the very least, the
following is needed:

```python
# /var/www/trendlines/trendlines.cfg
SECRET_KEY = b"don't use the value written in this README file!"
DATABASE = "/data/internal.db"
```

You should be all set to bring Docker Compose up:

```bash
$ docker-compose -f path/to/docker-compose.yml up -d
```

Again, open up a browser to `http://localhost` and you're good to go. Add some
data as outlined below and start playing around.

**Note:** If you get an error complaining about "Error starting userland proxy:
Bind for 0.0.0.0:80: Unexpected error Permission denied", then try changing
the port in docker-compose.yml to something else. I like 5000 myself:

```yaml
ports:
  - 5000:80
```


### Running behind a proxy

A typical case, for me at least, is adding this application to a server that's
already running Apache for other things. In this case, make the following
adjustments:

1.  Add a proxy to the `VirtualHost` in your apache config.
2.  Make sure to set the `URL_PREFIX` variable in your Trendlines config file.

```apache
# /etc/apache2/sites-enabled/your-site.conf
<VirtualHost *:80>
...
    # optionally replace all instances of "trendlines" with whatever you want
    # Make sure the port on ProxyPass and ProxyPassReverse matches what is
    # exposed in your docker-compose.yml file.
    <Location /trendlines>
        ProxyPreserveHost On
        ProxyPass http://0.0.0.0:5082/trendlines
        ProxyPassReverse http://0.0.0.0:5082/trendlines

        RequestHeader set X-Forwarded-Port 80
    </Location>
</VirtualHost>
```

```python
# /var/www/trendlines/trendlines.cfg
URL_PREFIX = "/trendlines"    # Whatever you put in your Apache proxy
```


### Running with Celery

Add the following services to your `docker-compose.yml`:

```yaml
redis:
  image: redis
  ports:
    - "6379:6379"
celery:
  image: dougthor42/trendlines:latest
  ports:
    - "9999:9999"
  volumes:
    # should be the same as what's in the 'trendlines' service
    - type: bind
      source: /var/www/trendlines
      target: /data
  command: celery worker -l info -A trendlines.celery_app.celery
```


## Upgrading

### Docker

Upgrading via pure Docker is not supported, as that's intended to only be
used as a preview. Please see Docker-Compose.


### Docker Compose

Upgrading `trendlines` when running in Docker Compose is as easy as pulling
the new image. Upgrading should take less than 5 minutes, depending on your
connection speed.

1.  Update your `docker-compose.yml` file if needed.
2.  Bring down your service. We don't want anything trying to write changes
    while we're doing things.
3.  Backup your database.
4.  Pull the new image.
5.  Perform database migrations.
6.  Bring up the stack.

If you're using a specific version release, update your `docker-compose.yml`
file:

```yaml
image dougthor42/trendlines:1.1
```

**Note:** Make sure to update the version in both the `trendlines` service
**and the `celery` service.**

If you're using the `latest` docker tag, which points to the latest git-tagged
release, then no changes to `docker-compose.yml` are needed.

Then run the rest of the steps:

```bash
cd /var/www/trendlines
docker-compose down
cp internal.db internal.db.bak
docker-compose pull

# Optional: See what migrations are missing
docker-compose run --rm --no-deps trendlines \
    peewee-db \
        --directory /trendlines/migrations \
        --database sqlite:///data/internal.db \
        status

# Run the migrations
docker-compose run --rm --no-deps trendlines \
    peewee-db \
        --directory /trendlines/migrations \
        --database sqlite:///data/internal.db \
        upgrade
docker-compose up -d
```


## Usage

TODO.


### Sending Data

**Trendlines** accepts 2 forms of data entry: TCP and UDP. TCP data entry is
done via HTTP POST with a JSON payload. UDP data entry is done in a similar
manner as Graphite (though not yet implemented).

To send in data using the HTTP POST method:

```bash
curl --data '{"metric": "foo.bar", "value": 52.88, "time": '${date +%s}'}' \
     --header "Content-Type: application/json" \
     --request POST \
     http://$SERVER/api/v1/data`
```

Or via UDP:

```bash
echo "foo.bar 52.88 `date +%s`" | nc $SERVER $PORT
```

The UDP string must follow the format `metric_name value timestamp`. This
is the same format that Graphite uses for their [plaintext
protocol](https://graphite.readthedocs.io/en/latest/feeding-carbon.html#the-plaintext-protocol),
so it is easy to switch from **Trendlines** to Graphite.


### Viewing Data

**Trendlines** creates a simple set of web pages. A landing page at
`http://$SERVER` provides a list of all known metrics. Clicking on a known
metric shows you the graph of historical data.

You can also export the data as JSON by sending an HTTP GET request:

```
curl http://$SERVER/api/v1/data/$METRIC_NAME
```


## Development

Assumptions:

+ Docker and Docker-compose are installed and up-to-date
+ Python 3.6 or higher


### Running with scripts

Make sure the `config/localhost.cfg` file exists:

```python
# ./config/localhost.cfg
DEBUG = True
DATABASE = "./internal.db"
TRENDLINES_API_URL = "http://localhost:5000/api/v1/data"
broker_url = "redis://localhost"
```

In 3 separate shells, run these 3 commands in order

1.  `docker run -p 6379:6379 redis`
2.  `python runserver.py`
3.  `python runworker.py`

You can also optionally run each in the background (`-d` for docker and
`&` for the others), but personally I like to see the logs scroll by.

From a 4th shell, send data:

```shell
echo "metric.name 12.345 `date +%s`" | nc localhost 9999
```

And view the data by opening `http://localhost:5000` in your browser.


### Running with Docker-Compose

The default configuration assumes running within docker-compose. If you need
different settings, create `config/trendlines.cfg` and add your variables
to it.

Build the images and bring up the stack:

```shell
$ docker-compose -f docker-build.yml build
$ docker-compose -f docker-build.yml up
```

Send data in

```shell
echo "metric.name 12.345 `date +%s`" | nc localhost 9999
```

And view the data by opening `http://localhost:5000` in your browser.


### Building Docker image

This is handled in CI, but in case you need to do it manually:

```shell
docker build -f docker/Dockerfile -t trendlines:latest -t dougthor42/trendlines:latest .
docker push dougthor42/trendlines:latest
```


### Database Migrations

This project uses [`peewee-moves`](https://github.com/timster/peewee-moves)
to handle migrations. The documentation for that project is a little lacking,
but I found it a litte easier to use than the more-popular
[`peewee-migrate`](https://github.com/klen/peewee_migrate). `peewee-moves`
also has more documentation.

To apply migrations to an exsiting database that has ***never had any
migrations applied***:

1.  Open up the database
2.  Manually create the following table (adjust syntax accordingly):
    ```sql
    CREATE TABLE migration_history (
      `id` INT NOT NULL AUTO_INCREMENT,
      `name` VARCHAR(255) NOT NULL,
      `date_applied` DATETIME NOT NULL,
      PRIMARY_KEY (`id`));
    ```
3.  Populate the table with all the migrations that have already been
    applied. The `name` value should match the migration filename, sans `.py`
    extension, and the `date_applied` field can be any timestamp.
    ```sql
    INSERT INTO `migration_history`
      (`name`, `date_applied`)
      VALUES
        ('0001_create_table_metric', '2019-02-14 14:56:37'),
        ('0002_create_table_datapoint', '2019-02-14 14:56:37');
    ```
4.  Verify that things are working. You should see `[x]` for all migrations:
    ```shell
    peewee-db --directory migrations --database sqlite:///internal.db status
    ```


#### Creating a new Table

1.  Create the table in `trendlines.orm`.
2.  Create the new table migration:
    ```shell
    $ peewee-db --directory migrations \
                --database sqlite:///internal.db \
                create \
                trendlines.orm.NewTable
    ```
3.  And then apply it:
    ```shell
    $ peewee-db --directory migrations \
                --database sqlite:///internal.db \
                upgrade
    ```

If you're using the python shell, run the following for for step 3:
```python
>>> from peewee import SqliteDatabase
>>> from peewee_moves import DatabaseManager
>>> manager = DatabaseManager(SqliteDatabase('internal.db')
>>> manager.create('trendlines.orm')
>>> manager.upgrade()
```


#### Modifying a table:

1.  Modify the table in `trendlines.orm`.
2.  Create the migration file:
    ```shell
    $ peewee-db --directory migrations \
                --database sqlite:///internal.db \
                revision
                "short_revision_description spaces OK but not recommended"
    ```
3.  Manually modify the `upgrade` and `downgrade` scripts in the new
    migration file.
4.  Apply the migration:
    ```shell
    $ peewee-db --directory migrations \
                --database sqlite:///internal.db \
                upgrade
    ```
