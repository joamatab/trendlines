# Changelog for Trendlines


## Unreleased
+ Integration tests (via docker-compose) were added. (#165)
+ Supposedly fixed an issue that occurs when running behind a proxy (#162).
+ *Actually* fixed the issue where the plots wouldn't show when `URL_PREFIX`
  was set (running behind a proxy). (#162).
  + Of course, there's another part which is **not** fixed (#168)
+ Redis was pinned at v5.0.5-alpine. (#163)


## 0.6.0b2 (2019-06-27)
+ Fixed a major issue where dataloss would occur when performing database
  migration 0005 -> 0006. (#158)
+ Links to the Swagger/ReDoc API documentation are now provided on the main
  page. (#152)
+ Fixed small error in development documentation. (#153)
+ Plots are now all shown on a single page, thus making it much easier to
  navigate between plots. (#58)
  + Added Bootstrap4
  + updated the jstree data structure to use internal ID instead of a
    generated URL (#156)


## 0.6.0b1 (2019-05-01)

### Notes
This revision contains some breaking API changes.

### Changes
+ `create_db` was moved out of `app_factory.py` and into `orm.py`. (#115)
+ All files created during tests are now made in the `/tmp` directory. (#44)
+ Migrations are now performed automatically when the flask app is created
  (when the first request comes in to WSGI). (#71, #114)
+ Dropped support for Python 3.5 (#119)
+ Added the REST API to get all metrics (#120)
+ `db.add_data_point` was renamed to `db.insert_datapoint` to match with
  future API naming conventions. (#123)
+ Added an internal api for datapoints to `db.py`. (#125)
+ The REST api is now viewable via a Swagger (or ReDoc!) web page! (#34)
+ Core API routes have been refactored to use Flask's Pluggable Views. (#128)
+ Sorted the Swagger API into logical blueprints by Schema/MethodView. (#133)
+ Replaced all instances of port 9999 with port 2003. (#104)
+ The `missing_required_key` error response now accepts lists or tuples.
  (#137)
+ The `/data` API routes have been moved to a MethodView class. (#138)
+ **BREAKING** The api has been refactored to be more consistent. Public API
  on core schemas (`Metric`, `DataPoint`) will only accept internal IDs and
  no longer accept strings for metric identification. See the docs for
  additional details. (#140)
+ Minor updates to how the `populated_db` test fixture works (#142)
+ Table PKs are now explicit `AUTOINCREMENT` rather than using SQLite's
  internal `ROWID`. This will result in increased cpu/memory/disk overhead,
  but it ensures that PKs cannot be resued. (#143)
+ The REST API for `DataPoint` has been implemented. (#122)
+ Example `docker-compose.yml` file now includes `depends_on`. (#99)
+ A tip on generating a secure secret has been added to the installation
  docs. (#93)
+ Command line stuff is now handled by `click`. (#150)


## 0.5.0 (2019-02-28)

### Notes
Upgrading from 0.4.0 to 0.5.0 breaks the migration history of the
database. **Automatic upgrades are not supported.** In order to correctly
upgrade without losing your data, follow these instructions (assuming
docker-compose):

> Note: you may need to add `sudo` to most of these.

1.  Bring `trendlines` down: `docker-compose down`.
2.  Backup your database: `cp internal.db internal.db_old`
3.  Pull the new `trendlines` code: `docker-compose pull`
4.  Delete your old DB and make a new, empty database file (see issue #110):
    ```bash
    $ rm internal.db
    $ touch internal.db
    $ chown www-data:www-data internal.db
    ```
5.  Run the migrations on this new file:
    ```bash
    $ docker-compose run --rm --no-deps trendlines \
          peewee-db \
              --directory /trendlines/migrations \
              --database sqlite:///data/internal.db \
              status
    $ docker-compose run --rm --no-deps trendlines \
          peewee-db \
              --directory /trendlines/migrations \
              --database sqlite:///data/internal.db \
              upgrade
    ```
    You should see the following outputs, perhaps with a "Creating network"
    thrown in there from docker:
    ```
    INFO: [ ] 0001_create_table_metric
    INFO: [ ] 0002_create_table_datapoint
    INFO: [ ] 0003_add_spec_limits
    INFO: [ ] 0004_unique_constraint_metric_name
    INFO: [ ] 0005_on_delete_cascade_metric

    INFO: upgrade: 0001_create_table_metric
    INFO: upgrade: 0002_create_table_datapoint
    INFO: upgrade: 0003_add_spec_limits
    INFO: upgrade: 0004_unique_constraint_metric_name
    INFO: upgrade: 0005_on_delete_cascade_metric
    ```
6.  Copy your data from the old file to the new:
    ```
    $ sqlite3 internal.db
    sqlite> ATTACH 'internal.db_old' as old;
    sqlite> INSERT INTO metric SELECT * FROM old.metric;
    sqlite> INSERT INTO datapoint SELECT * FROM old.datapoint;
    sqlite> .q
    ```
7.  Bring up `trendlines`: `docker-compose up -d`
8.  Verify that you can add a new metric and datapoint:
    ```bash
    $ echo "some-new-metric-name 99" | nc $SERVER $PORT
    ```

### Changes
+ Fixed an issue with migrations (#112).


## 0.4.0 (2019-02-26)

### New Features
+ Added columns to the `Metric` table to support limits. (#65)
+ Many more API routes have been added:
    + `GET /api/v1/metric/<metric_name>` has been implemented (#73)
    + `DELETE /api/v1/metric/<metric_name>` has been implemented (#78)
    + `POST /api/v1/metric` has been implemented (#74)
    + `PUT /api/v1/metric/<metric_name>` has been implemented (#75)
    + `PATCH /api/v1/metric/<metric_name>` has been implemented (#83)
    + `DELETE /api/v1/datapoint/<datapoint_id>` has been implemented (#57)
+ Implemented database migrations (#62)
+ The program version is now displayed on all pages. (#109)
+ The tree is now auto-expanded by default. (#105)

### Changes
+ Changed (again) how we handle being behind a proxy. (#60)
+ DB migrations are now inlcuded in the docker image, and documentation
  was added on how to perform upgrades. (#67)
+ The `Metric.name` column is now forced to be unique. Previously this was
  enforced on the software side, but not on the database side. (#66)
+ The `DataPoint.metric_id` foreign key is now set to CASCADE on deletes (#69)
+ Error responses for the REST API have been refactored (#85)
+ Additional tests for PUT/PATCH metric have been added (#86)
+ Make use of peewee's `playhouse` extensions for converting model instances
  to and from dicts. (#87)
+ `peewee-moves` was updated to v2.0.1.
+ Documentation is now reStructuredText and is hosted by ReadTheDocs (#91)
+ Switched to using `loguru` for logging. (#94)
+ Renamed some function arguments to be more clear. (#89)
+ Removed a hack that caused plot urls to be generated client-side. Was
  blocking #47. (#100)
+ Moved javascript out of HTML files. (#47)


## v0.3.0 (2019-01-28)
+ `units` are now also returned in the GET `/data` API call.
+ Removed a confusing route: `/api/v1/<metric>`. (#39)
+ Added a title that will link back to the index page. (#40)
+ Changed the way we handle generating links when behind a proxy that's
  mucking about with the URLs. (#41)
+ Units will now be displayed on the y-axis if they exist. (#37)
+ `routes.format_data` was moved to the `utils` module.
+ Added support for optional Celery workers that accept TCP data, allowing
  for easier transition from `Graphite`. (#6)


## v0.2.0 (2019-01-14)
+ [BREAKING] Updated REST API: "add" and "get" changed to "data". The HTTP
  method will be used to determine adding or retrieving.
+ Implemented switching between sequential and time-series data. (#8).
+ Plot link generation has been moved client-side. This fixes an issue where
  links would not work when an external force modifies the URL. Fixes #33.


## v0.1.1 (2019-01-10):
Simply a version bump to verify deployment to PyPI from Travis-CI.


## v0.1.0 (2019-01-10): Preview Release
This is a preview release with the core functionality:

+ Web page for viewing data with tree structure (#7)
+ Accept TCP entries via HTTP POST
+ Docker container for easy deployment (#9)
+ Unit and integration tests (#4)
+ Continuous Integration for tests (#10)

What's not included is:

+ Accept UDP data (#6)
+ Switch between by-number and by-time plots (#8)
+ Looking nice
+ UX enhancements
+ Multiple plots per page (#11)
+ Email alerting system (#12)
+ Continuous Delivery to PyPI and Docker Hub


## v0.0.0 (2018-12-20)
+ Project Creation
