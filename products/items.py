import copy
import dataclasses
import json
from datetime import datetime
from typing import List, Mapping, Any, get_origin

from bson import ObjectId

from products.exceptions import ValidationError


def _as_dict_inner(obj, dict_factory=dict):
    if dataclasses.is_dataclass(obj):
        mapping = obj.KEY_NAME_MAPPING
        result = []
        for f in dataclasses.fields(obj):
            value = _as_dict_inner(getattr(obj, f.name), dict_factory)
            result.append((mapping[f.name], value))
        return dict_factory(result)

    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_as_dict_inner(v, dict_factory) for v in obj])

    elif isinstance(obj, (list, tuple)):
        return type(obj)(_as_dict_inner(v, dict_factory) for v in obj)

    elif isinstance(obj, dict):
        return type(obj)((_as_dict_inner(k, dict_factory),
                          _as_dict_inner(v, dict_factory))
                         for k, v in obj.items())
    elif isinstance(obj, NotSet):
        return None
    else:
        return copy.deepcopy(obj)


def _validate(obj):
    errors_not_set = {}
    errors_type = {}
    queue = [obj]
    while queue:
        o = queue.pop(0)
        not_set_required_fields = copy.deepcopy(o.REQUIRED_FIELDS)
        type_error = []
        for field in dataclasses.fields(o):
            field_type = get_origin(field.type) or field.type
            field_value = getattr(o, field.name)
            if field_value != NOTSET and not isinstance(field_value, (field_type, type(None))):
                type_error.append({'field_name': field.name,
                                   'provided': str(type(field_value)),
                                   'must_be': str(field_type)})
            if field.name in not_set_required_fields and (field_value != NOTSET or field_value is not None):
                not_set_required_fields.remove(field.name)
            if dataclasses.is_dataclass(field_value):
                queue.append(field_value)
        if not_set_required_fields:
            errors_not_set[type(o)] = not_set_required_fields
        if type_error:
            errors_type[type(o)] = type_error

    errors = {}
    if errors_not_set:
        errors['required_fields_are_not_set'] = errors_not_set
    if errors_type:
        errors['types_are_wrong'] = errors_type
    if errors:
        raise ValidationError('Validation error.', details=errors)


class NotSet:
    def __repr__(self):
        return 'NOTSET'

    def __str__(self):
        return 'NOTSET'

    def __eq__(self, other):
        return isinstance(other, NotSet)


NOTSET = NotSet()


def default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, ObjectId):
        return str(o)


@dataclasses.dataclass
class BaseDataclass:
    KEY_NAME_MAPPING = {}
    REQUIRED_FIELDS = set()

    def validate(self):
        try:
            _validate(self)
        except ValidationError as e:
            raise ValidationError('%s %s', e.message, e.details, details=None)

    def as_dict(self):
        return _as_dict_inner(self)

    def json(self):
        return json.dumps(self.as_dict(), ensure_ascii=False, default=default)


@dataclasses.dataclass
class Store(BaseDataclass):
    KEY_NAME_MAPPING = {
        'id': 'id',
        'name': 'name',
        'address': 'store_address',
        'lat': 'lat',
        'lon': 'lon'
    }
    REQUIRED_FIELDS = {'id', 'name', 'address', 'lat', 'lon'}

    id: str = 'NOTSET'
    name: str = 'NOTSET'
    address: str = 'NOTSET'
    lat: str = 'NOTSET'
    lon: str = 'NOTSET'


@dataclasses.dataclass
class Product(BaseDataclass):
    KEY_NAME_MAPPING = {
        '_id': '_id',
        'doc_id': 'doc_id',
        'job_id': 'job_id',
        'vendor_name': 'vendor',
        'scrap_time': 'scrap_time',
        'id': 'id',
        'title': 'name',
        'brand': 'brand',
        'category': 'category',
        'base_price': 'basePrice',
        'discounted_price': 'discountedPrice',
        'url': 'url',
        'images': 'images',
        'count': 'count',
        'store': 'store',
        'description': 'description',
        'others': 'others'
    }
    REQUIRED_FIELDS = {'id', 'title', 'base_price', 'url', 'count'}

    _id: ObjectId = 'NOTSET'  # unique id universally
    doc_id: str = 'NOTSET'  # unique id in superz system
    job_id: str = 'NOTSET'
    vendor_name: str = 'NOTSET'
    scrap_time: datetime = 'NOTSET'

    id: str = 'NOTSET'
    title: str = 'NOTSET'
    brand: str = 'NOTSET'
    category: str = 'NOTSET'
    base_price: int = 'NOTSET'
    discounted_price: int = 'NOTSET'
    url: str = 'NOTSET'
    images: List[str] = 'NOTSET'
    count: int = 'NOTSET'
    store: Store = 'NOTSET'
    description: str = 'NOTSET'
    others: Mapping[Any, Any] = 'NOTSET'


