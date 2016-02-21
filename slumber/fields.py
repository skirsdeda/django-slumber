"""
    Integration between Slumber and Django models.
"""
from django.db.models import URLField, SubfieldBase

from slumber.connector.api import _InstanceProxy, get_instance
#from slumber.connector.dictobject import DictObject
from slumber.forms import RemoteForeignKeyField, TypedRemoteChoiceField
from slumber.scheme import to_slumber_scheme, from_slumber_scheme
from slumber.server import get_slumber_services

from django.utils.text import capfirst

class RemoteForeignKey(URLField):
    """Wraps Django's URLField to provide a field that references a remote
    object on another Slumber service.
    """
    # Django already has too many public methods and we can't change it
    # pylint: disable=R0904

    description = "A remote Slumber object."
    __metaclass__ = SubfieldBase

    def __init__(self, model_url, **kwargs):
        self.model_url = model_url
        super(RemoteForeignKey, self).__init__(**kwargs)

    def deconstruct(self):
        """Added to support Django 1.7 migrations
        """
        name, path, args, kwargs = super(RemoteForeignKey, self).deconstruct()
        if self.model_url != ",":
            kwargs['model_url'] = self.model_url
        return name, path, args, kwargs

    def run_validators(self, value):
        # Do not rely on validators as we want to support Django 1.0
        pass
    
    def validate(self, x, y):
        return

    def get_db_prep_value(self, value, *a, **kw):
        if value is None:
            url = None
        elif isinstance(value, basestring):
            url = to_slumber_scheme(value, get_slumber_services())
        else:
            url = to_slumber_scheme(value._url, get_slumber_services())
        res = super(RemoteForeignKey, self).get_db_prep_value(url, *a, **kw)
        return res

    def get_prep_value(self, value, *a, **kw):
        if isinstance(value, basestring) or value is None:
            return value
        url = to_slumber_scheme(value._url, get_slumber_services())
        return super(RemoteForeignKey, self).get_prep_value(url, *a, **kw)

    def to_python(self, value):
        if not value:
            return None
        if isinstance(value, _InstanceProxy):
            return value
        instance_url = from_slumber_scheme(
            super(RemoteForeignKey, self).to_python(value),
            get_slumber_services())
        model_url = from_slumber_scheme(
            self.model_url, get_slumber_services())
        return get_instance(model_url, instance_url, None)

    def parent_formfield(self, form_class=None, choices_form_class=None, **kwargs):
        """
        Returns a django.forms.Field instance for this database Field.
        """
        defaults = {'required': not self.blank,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text}
        if self.has_default():
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True
            else:
                defaults['initial'] = self.get_default()
        if self.choices:
            # Fields with choices get special treatment.
            include_blank = (self.blank or
                             not (self.has_default() or 'initial' in kwargs))
            defaults['choices'] = self.get_choices(include_blank=include_blank)
            defaults['coerce'] = self.to_python
            if self.null:
                defaults['empty_value'] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
            # Many of the subclass-specific formfield arguments (min_value,
            # max_value) don't apply for choice fields, so be sure to only pass
            # the values that TypedChoiceField will understand.
            for k in list(kwargs):
                if k not in ('coerce', 'empty_value', 'choices', 'required',
                             'widget', 'label', 'initial', 'help_text',
                             'error_messages', 'show_hidden_initial', 'model_url'):
                    del kwargs[k]
        defaults.update(kwargs)
        if form_class is None:
            form_class = forms.CharField
        return form_class(**defaults)

    def formfield(self, **kwargs):
        defaults = {'form_class': RemoteForeignKeyField,
            'model_url': self.model_url}
        defaults.update(kwargs)
        defaults['choices_form_class'] = TypedRemoteChoiceField
        #copied because kwargs for choice field are hardcoded but we need model_url
        res = self.parent_formfield(**defaults) 
        return res


try:
    # If South in installed then we need to tell it about our custom field
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([
            (
                (RemoteForeignKey,),
                [],
                {'model_url': ('model_url', {})}
            )
        ], [r"^slumber\.fields\.RemoteForeignKey"])
except ImportError: # pragma: no cover
    # South isn't installed so don't worry about it
    pass

