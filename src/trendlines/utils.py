# -*- coding: utf-8 -*-
"""
"""
from contextlib import contextmanager

from flask import current_app
from flask import jsonify


class Rfc7807ErrorResponse(object):
    """
    An error response object that (mostly) conforms to `RFC 7807`_.

    Parameters
    ----------
    type_ : str
        A URI reference that identifies the problem type. Typically is a link
        to human-readable documentation for the problem type.
    title : str, optional
        A short, human-readable summary of the problem type. It SHOULD NOT
        change from occurrence to occurence, except for the purposes of
        localization.
    status : int, optional
        The HTTP status code generated by the origin server.
    detail : str, optional
        A human-readable explaination specific to this occurence of the
        problem.
    instance : str, optional
        A URI reference that identifies the specific occurence of the
        problem.
    others : dict
        Additional key-value pairs to be returned.

    _`RCF 7807`: https://tools.ietf.org/html/rfc7807
    """
    _content_type = "application/problem+json"

    def __init__(self, type_, title=None, status=None, detail=None,
                 instance=None, **kwargs):
        # Required
        self.type = type_
        # Recommended
        self.title = title
        self.status = status
        self.detail = detail
        # Optional
        self.instance = instance

        self.others = kwargs

    @property
    def content_type(self):
        return Rfc7807ErrorResponse._content_type

    def as_dict(self):
        """
        Return this object as a Python dictionary.
        """
        d = {"type": self.type}
        other_keys = ['title', 'status', 'detail', 'instance']
        for k in other_keys:
            if getattr(self, k) is not None:
                d[k] = getattr(self, k)

        return {**d, **self.others}

    def as_response(self):
        """
        Return this object as a flask Response object.

        Note that this will only work within a application context.

        The only difference between this and ``flask.jsonify`` is that the
        mimetype is modified to fit with RFC 7807.
        """
        with adjust_jsonify_mimetype(self.content_type):
            return jsonify(self.as_dict())


@contextmanager
def adjust_jsonify_mimetype(new_type):
    """
    Context Manager. Temporarily adjust the application's JSONIFY_MIMETYPE.

    Must be run within an application context, as it uses ``current_app``.

    Parameters
    ----------
    new_type : str
        The new Content-Type / Mimetype to use during ``jsonify``.
    """
    var_name = 'JSONIFY_MIMETYPE'
    old = current_app.config[var_name]
    current_app.config[var_name] = new_type
    yield
    current_app.config[var_name] = old


def get_metric_parent(metric):
    """
    Determine the parent of a metric.

    If no parent exists, the root ``#`` is given.

    Parameters
    ----------
    metric : str
        The dotted metric to act on.

    Returns
    -------
    parent : str

    Examples
    --------
    >>> get_metric_parent("foo")
    "#"
    >>> get_metric_parent("foo.bar")
    "foo"
    >>> get_metric_parent("foo.bar.baz.foo")
    "foo.bar.baz"
    """
    s = metric.split(".")
    if len(s) == 1:
        # top-level item. parent is "#" (root)
        parent = "#"
    else:
        parent = ".".join(s[:-1])

    return parent


def format_metric_for_jstree(metric):
    """
    Format a metric name into a dict consumable by jsTree.

    See "Alternative JSON format" in the `jsTree docs`_.

    .. _`jsTree docs`: https://www.jstree.com/docs/json/

    Parameters
    ----------
    metric : str
        The metric name to format.

    Returns
    -------
    dict
        A dict with the following keys: id, parent, text, is_link
    """
    parent = get_metric_parent(metric)
    return {"id": metric, "parent": parent, "text": metric, "is_link": True}


def build_jstree_data(metrics):
    """
    Build a list of dicts consumable by jsTree.

    Fills in missing parent nodes and gives them a ``"is_link": False`` item.

    Parameters
    ----------
    metrics : list of str
        The metrics to display as returned by :func:`db.get_metrics`.

    Returns
    -------
    data : list of dict
        A JSON-serializable list of dicts. Each dict has at least ``id`` and
        ``parent`` keys. If the metric doesn't exist (it's just a placeholder
        parent), then the dict will have the ``"is_link": False`` item.

    Notes
    -----
    Given the following metrics::

        foo
        foo.bar
        bar.baz.biz

    The return value of this function will be:

    .. code-block:: python

       # Spacing added for readability
       # The `text` key is removed for readabiity.
       [
        {"id": "foo",         "parent": "#",       "is_link": True },
        {"id": "foo.bar",     "parent": "foo",     "is_link": True },
        {"id": "bar",         "parent": "#",       "is_link": False},
        {"id": "bar.baz",     "parent": "bar",     "is_link": False},
        {"id": "bar.baz.biz", "parent": "bar.baz", "is_link": True },
       ]
    """
    # First go through and make all of our existing links
    data = [format_metric_for_jstree(m) for m in metrics]

    # then search through that data and find any missing parents.
    for m in data:
        parent = m["parent"]

        # ignore root nodes and parents that already exist.
        if parent == "#" or parent in (x['id'] for x in data):
            continue

        # Create the grandparent
        new_parent = get_metric_parent(parent)

        # Add the new, non-linked item to our data. Yes we're intentionally
        # modifying the array we're looping over so that we make sure to
        # get all parents no matter how deep.
        new = {"id": m['parent'],
               "parent": new_parent,
               "text": m['parent'],
               "is_link": False}
        data.append(new)

    # Lastly sort things in a predictable fashion.
    data.sort(key=lambda d: d['id'])
    return data