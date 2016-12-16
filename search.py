import logging
import inspect
from google.appengine.api import search as search_api
from google.appengine.ext import ndb


def _datetime_coverter(n, v):
    date = search_api.DateField(name=n, value=v)
    iso = search_api.TextField(name=n + '_iso', value=v.isoformat())
    return date, iso


property_to_field_map = {
    ndb.IntegerProperty: lambda n, v: search_api.NumberField(name=n, value=v),
    ndb.FloatProperty: lambda n, v: search_api.NumberField(name=n, value=v),
    ndb.BooleanProperty: lambda n, v: search_api.AtomField(name=n, value='true' if v else 'false'),
    ndb.StringProperty: lambda n, v: search_api.TextField(name=n, value=v),
    ndb.TextProperty: lambda n, v: search_api.TextField(name=n, value=v),
    # BlobProperty explicitly unindexable
    ndb.DateTimeProperty: _datetime_coverter,
    ndb.DateProperty: lambda n, v: search_api.DateField(name=n, value=v),
    ndb.TimeProperty: lambda n, v: search_api.TextField(name=n, value=v.isoformat()),
    ndb.GeoPtProperty: lambda n, v: search_api.GeoField(name=n, value=search_api.GeoPoint(v.lat, v.lon)),
    # KeyProperty explicity unindexable
    # BlobKeyProperty explicitly unindexable
    ndb.UserProperty: lambda n, v: search_api.TextField(name=n, value=unicode(v)),
    # StructuredProperty explicitly unindexable
    # LocalStructuredProperty explicitly unindexable
    # JsonProperty explicitly unindexable
    # PickleProperty explicity unindexable
    # GenericProperty explicitly unindexable
    # ComputedProperty explicitly unindexable
}

non_repeatable_properties = (
    ndb.DateTimeProperty,
    ndb.DateProperty,
    ndb.TimeProperty,
    ndb.IntegerProperty,
    ndb.FloatProperty
)


def default_entity_indexer(instance, properties, extra_converters=None):
    results = []

    converters = {}
    converters.update(property_to_field_map)
    if extra_converters:
        converters.update(extra_converters)

    for property in properties:
        value = getattr(instance, property)
        converted = None
        property_instance = instance._properties[property]
        property_class = property_instance.__class__
        converter = converters.get(property_class, converters.get(property, None))

        if not value or not converter:
            if property_class in (ndb.KeyProperty, ndb.BlobKeyProperty):
                logging.debug('Search utilities will not automatically index Key or BlobKey property %s' % property)
            continue

        if not property_instance._repeated:
            converted = converter(property, value)
        else:
            if not property_class in non_repeatable_properties:
                converted = [converter(property, x) for n, x in enumerate(value)]
            else:
                logging.debug('Could not automatically add field %s to the index because date and number fields can not be repeated.' % property)

        if not converted:
            continue

        if isinstance(converted, (list, tuple)):
            results.extend(converted)
        else:
            results.append(converted)

    return results


def index_entity(instance, index, only=None, exclude=None, extra_converters=None, indexer=None, callback=None):
    """
    Adds an Model instance into full-text search indexes.

    :param instance: an instance of ndb.Model
    :param list(string) only: If provided, will only index these fields
    :param list(string) exclude: If provided, will not index any of these fields
    :param dict extra_converters: Extra map of property names or types to converter functions.
    :param indexer: A function that transforms properties into search index fields.
    :param callback: A function that will recieve (instance, fields).
        Fields is a map of property names to search.Field instances generated by the indexer
        the callback can modify this dictionary to change how the item is indexed.

    This is usually done in :meth:`Model.after_put <argeweb.core.ndb.Model.after_put>`, for example::

        def after_put(self):
            index(self)

    """

    indexer = indexer if indexer else default_entity_indexer
    indexes = index if isinstance(index, (list, tuple)) else [index]
    only = only if only else [k for k in instance._properties.keys() if hasattr(instance, k)]
    exclude = exclude if exclude else []
    properties = [x for x in only if x not in exclude]

    fields = indexer(instance, properties, extra_converters=extra_converters)

    if callback:
        callback(instance=instance, fields=fields)

    try:
        doc = search_api.Document(doc_id=str(instance.key.urlsafe()), fields=fields)

        for index_name in indexes:
            index = search_api.Index(name=index_name)
            index.put(doc)

    except Exception as e:
        logging.error('Adding model %s instance %s to the full-text index failed' % (instance.key.kind(), instance.key.id()))
        logging.error('Search API error: %s' % e)
        logging.debug([(x.name, x.value) for x in fields])


def unindex_entity(instance_or_key, index=None):
    """
    Removes a document from the full-text search.

    This is usually done in :meth:`Model.after_delete <argeweb.core.ndb.Model.after_delete>`, for example::

        @classmethod
        def after_delete(cls, key):
            unindex(key)

    """
    if isinstance(instance_or_key, ndb.Model):
        instance_or_key = instance_or_key.key

    indexes = index if isinstance(index, (list, tuple)) else [index]

    for index_name in indexes:
        index = search_api.Index(name=index_name)
        index.delete(str(instance_or_key.urlsafe()))


def transform_to_entities(results):
    """
    Transform a list of search results into ndb.Model entities by using the document id
    as the urlsafe form of the key.
    """
    results = ndb.get_multi([ndb.Key(urlsafe=x.doc_id) for x in results])
    results = [x for x in results if x]
    return results


def search(index, query, limit=None, cursor=None, options=None, sort_field=None, sort_direction='asc', sort_default_value=None, per_document_cursor=False, transformer=transform_to_entities):
    """
    Searches an index with the given query.

    By default, this will transform the results into a list of datastore
    entities. This behavior can be override by providing a function to the transformer argument.

    Additionally, this only gets document ids by default. To override this, pass in an options parameter that
    sets ids_only to False.

    example of disabling both of these default behaviors:

        search(index='test_index', query='test', options={'ids_only': False}, transformer=list)

    This function returns a tuple: error, results, cursor, next_cursor.
    """

    options = options if options else {}
    error = None
    results = []
    current_cursor = None
    next_cursor = None

    try:
        index = search_api.Index(name=index)
        current_cursor = search_api.Cursor(web_safe_string=cursor) if cursor else search_api.Cursor(per_result=per_document_cursor)

        options_params = dict(
            limit=limit,
            ids_only=True,
            cursor=current_cursor)

        if sort_field:
            options_params['sort_options'] = create_sort_options(sort_field, sort_direction, sort_default_value)

        options_params.update(options)

        # if limit is none, remove it, as it'll cause issues.
        if options_params.get('limit') is None:
            del options_params['limit']

        query = search_api.Query(query_string=query, options=search_api.QueryOptions(**options_params))
        index_results = index.search(query)

        results = transformer(index_results)

        current_cursor = current_cursor.web_safe_string if current_cursor else None
        next_cursor = index_results.cursor.web_safe_string if index_results.cursor and results else None

    except (search_api.Error, search_api.query_parser.QueryException) as e:
        error = str(e)

    return error, results, current_cursor, next_cursor


def create_sort_options(field, direction='asc', default_value=None):
    direction_exp = search_api.SortExpression.ASCENDING if direction == 'asc' else search_api.SortExpression.DESCENDING

    if inspect.isfunction(default_value):
        default_value = default_value(field, direction)

    return search_api.SortOptions(expressions=[
        search_api.SortExpression(
            expression=field,
            direction=direction_exp,
            default_value=default_value or ''
        )
    ])


def join_query(filters, operator='AND', parenthesis=False):
    """
    Utility function for joining muliple queries together
    """
    operator = ' %s ' % operator
    filters = [x for x in filters if x]
    if parenthesis:
        filters = ['(%s)' % x for x in filters]
    return operator.join(filters)
