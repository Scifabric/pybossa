from flask_babel import lazy_gettext
from flask_wtf import FlaskForm as Form
import wtforms


def form_builder(form_name, form_config):
    new_form = type(form_name, (Form,), {})

    for field_name, field_config in form_config:
        input_field = build_field(*field_config)
        setattr(new_form, field_name, input_field)

    return new_form


def build_field(field_type, description, validators, kwargs=None):
    kwargs = kwargs or {}
    field_class = getattr(wtforms, field_type)
    return field_class(lazy_gettext(description), **kwargs)
