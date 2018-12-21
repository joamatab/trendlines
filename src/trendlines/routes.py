# -*- coding: utf-8 -*-

import json
from datetime import datetime
from datetime import timezone

from flask import Blueprint
from flask import render_template
from flask import request

# peewee
from playhouse.shortcuts import model_to_dict

from . import db

pages = Blueprint('pages', __name__)
api = Blueprint('api', __name__)


@pages.route('/', methods=['GET'])
def index():
    """
    Main page.

    Displays a list of all the known metrics with links.
    """
    data = db.get_metrics()
    return render_template("trendlines/index.html", data=data)


@pages.route("/plot/<metric>", methods=["GET"])
def plot(metric=None):
    """
    Plot a given metric.
    """
    if metric is None:
        return "Need a metric, friend!"

    data = get_data(metric)
    if len(data) == 0:
        return "Metric '{}' wasn't found. No data, maybe?".format(metric)

    # TODO: Ajax request for this data instead of sending it to the template.
    return render_template('trendlines/plot.html', name=metric, data=data)


@api.route("/api/v1/add", methods=['POST'])
def add():
    """
    Add a new value and possibly a metric if needed.

    Expected JSON payload has the following key/value pairs::

      metric: string
      value: numeric
      time: integer or missing
    """
    data = request.get_json()

    try:
        metric = data['metric']
        value = data['value']
    except KeyError:
        print("Missing 'metric' or 'value'.")
        return "error", 400

    time = data.get('time', None)

    db.add_metric(metric)
    new = db.add_data_point(metric, value, time)

    msg = "Added DataPoint to Metric {}\n".format(new.metric_id)
    return msg, 201


# TODO: Rename this function. It's too easy to get confused with db.get_data
def get_data(metric):
    """
    Helper function: query data, format for template consumption.

    Parameters
    ----------
    metric : str
        The metric name to get data for.

    Returns
    -------
    data : dict
        Dictionary of data where ``timestamp`` is a POSIX integer timestamp.
    """
    data = db.get_data(metric)
    data = [{'timestamp': row.timestamp.timestamp(),
             'value': row.value,
             'id': row.datapoint_id,
             'n': n}
            for n, row in enumerate(data)]
    return {'rows': data}
