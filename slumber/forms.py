"""
    Contains widgets used for Slumber.
"""
from django import forms
from django.contrib.admin.widgets import AdminURLFieldWidget

from slumber.connector.api import _InstanceProxy, get_instance
from slumber.scheme import from_slumber_scheme
from slumber.server import get_slumber_services
import copy
from slumber.scheme import to_slumber_scheme, from_slumber_scheme
from slumber.server import get_slumber_services

class RemoteForeignKeyWidget(forms.TextInput):
    """A widget that allows the URL to be edited.
    """
    def render(self, name, value, **kw):
        if isinstance(value, basestring):
            return super(RemoteForeignKeyWidget, self).render(
                name, value, **kw)
        else:
            return super(RemoteForeignKeyWidget, self).render(
                name, value._url if value else None, **kw)


class RemoteForeignKeyField(forms.Field):
    """A simple widget that allows the URL for the remote object to be
    seen and edited.
    """
    def __init__(self, max_length=None, verify_exists=True,
            model_url=None, **kwargs):
        assert model_url, "RemoteForiegnKeyField must be passed a model_url"
        self.max_length = max_length
        self.model_url = model_url
        self.verify_exists = verify_exists
        default = {'widget': RemoteForeignKeyWidget}
        default.update(kwargs)
        if default['widget'] == AdminURLFieldWidget:
            # We have to ignore a request for admin's broken widget
            default['widget'] = RemoteForeignKeyWidget
        super(RemoteForeignKeyField, self).__init__(**default)

    def clean(self, value):
        if not value:
            if self.required:
                raise forms.ValidationError('This field is required')
            return None
        elif isinstance(value, _InstanceProxy):
            return value
        else:
            try:
                model_url = from_slumber_scheme(
                    self.model_url, get_slumber_services())
                instance = get_instance(model_url, value, None)
                unicode(instance)
            
            except AssertionError:
                raise forms.ValidationError("The remote object doesn't exist")
            return instance

from django.forms.widgets import Select
class RemoteSelect(Select):
    def render(self, name, value, attrs=None, choices=()):
        # we had to cast slumber field to string
        if value is not None:
            value = to_slumber_scheme(value._url, get_slumber_services())
        return super(RemoteSelect, self).render(name, value, attrs=attrs, choices=choices)       

class TypedRemoteChoiceField(RemoteForeignKeyField):
    def __init__(self, coerce=None, *args, **kwargs):
        self.empty_value = kwargs.pop('empty_value', '')
        kwargs['widget'] = RemoteSelect()
        choices = kwargs.pop('choices', [])
        super(TypedRemoteChoiceField, self).__init__(*args, **kwargs)
        self.choices = choices

    def __deepcopy__(self, memo):
        result = super(TypedRemoteChoiceField, self).__deepcopy__(memo)
        result._choices = copy.deepcopy(self._choices, memo)
        return result

    def _get_choices(self):
        return self._choices

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        self._choices = self.widget.choices = list(value)

    choices = property(_get_choices, _set_choices)
    
    def to_python(self, value):
        if not value:
            return None
        if isinstance(value, _InstanceProxy):
            return value
        instance_url = from_slumber_scheme(
            super(TypedRemoteChoiceField, self).to_python(value),
            get_slumber_services())
        model_url = from_slumber_scheme(
            self.model_url, get_slumber_services())
        return get_instance(model_url, instance_url, None)
    
#     def to_python(self, value):
#         """
#         Validates that the value is in self.choices and can be coerced to the
#         right type.
#         """
#         value = super(TypedChoiceField, self).to_python(value)
#         if value == self.empty_value or value in self.empty_values:
#             return self.empty_value
#         try:
#             value = self.coerce(value)
#         except (ValueError, TypeError, ValidationError):
#             raise ValidationError(
#                 self.error_messages['invalid_choice'],
#                 code='invalid_choice',
#                 params={'value': value},
#             )
#         return value