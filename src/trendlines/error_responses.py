# -*- coding: utf-8 -*-
"""
"""
from enum import Enum

from flask import jsonify

from trendlines import logger
from . import utils


class ErrorResponseType(Enum):
    NO_DATA = 1
    NOT_FOUND = 2
    INVALID_REQUEST = 3
    ALREADY_EXISTS = 4
    INTEGRITY_ERROR = 5

    def __str__(self):
        return self.name.lower().replace("_", "-")

    @property
    def url(self):
        base = "https://trendlines.readthedocs.io/en/latest/error-responses"
        return f"{base}#{str(self)}"


class ErrorResponse(object):

    @classmethod
    def no_data(cls):
        """No data exists in the table."""
        detail = "No data found."
        return error_response(404, ErrorResponseType.NO_DATA, detail)

    @classmethod
    def metric_not_found(cls, name):
        detail = f"The metric '{name}' does not exist"
        return error_response(404, ErrorResponseType.NOT_FOUND, detail)

    @classmethod
    def datapoint_not_found(cls, datapoint_id):
        detail = f"The datapoint '{datapoint_id}' does not exist"
        return error_response(404, ErrorResponseType.NOT_FOUND, detail)

    @classmethod
    def metric_has_no_data(cls, name):
        detail = f"No data exists for metric '{name}'."
        return error_response(404, ErrorResponseType.NO_DATA, detail)

    @classmethod
    def metric_already_exists(cls, name):
        detail = f"The metric '{name}' already exists."
        return error_response(409, ErrorResponseType.ALREADY_EXISTS, detail)

    @classmethod
    def unique_metric_name_required(cls, old, new):
        detail = ("Unable to change metric name '{}': target name '{}'"
                  " already exists.")
        detail = detail.format(old, new)
        return error_response(409, ErrorResponseType.INTEGRITY_ERROR, detail)

    @classmethod
    def missing_required_key(cls, key):
        if isinstance(key, (list, tuple)):
            detail = f"Missing one of required keys: {key}"
        else:
            detail = f"Missing required key '{key}'"
        return error_response(400, ErrorResponseType.INVALID_REQUEST, detail)


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
        with utils.adjust_jsonify_mimetype(self.content_type):
            return jsonify(self.as_dict())


def error_response(http_status, type_, detail):
    """
    Create an error response for HTTP/JSON.

    This handles some of the minor implementation details of
    :class:`error_responses.Rfc7807ErrorResponse` such as passing around the http
    status code, logging, and setting the ``title`` value.

    Parameters
    ----------
    http_status : int
        The HTTP status code to return.
    type_ : :class:`error_responses.ErrorResponseType
        The general type of error.
    detail : str
        Specific error details, typically including how to resolve the issue.

    Returns
    -------
    (response, status_code)
        A two-tuple suitible for being the return value of a flask route.

    Notes
    -----
    The ``Title`` key for RFC8708 is currently derived from the type. This
    may change in the future.

    Example Usage
    -------------

    code-block:: python
      @app.route("/foo", methods=["GET"])
      def get_thing():
          try:
              thing = find_thing()
          except NotFound:
              return error_responses.error_response(
                  404,
                  error_responses.ErrorResponseType.NOT_FOUND,
                  "The thing was not found.",
              )
          return jsonify(thing), 200

    """
    title = type_.name
    resp = Rfc7807ErrorResponse(type_.url, title, http_status, detail)
    logger.warning(f"API error {title}: {detail}")
    return resp.as_response(), http_status
