from flask_babel import lazy_gettext
from flask_wtf import FlaskForm as Form
from wtforms import SelectField, validators
from pybossa.forms.fields.select_two import Select2Field

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

def dynamic_project_form(class_type, form_data, data_access_levels, obj=None):

    class ProjectFormExtraInputs(class_type):
        pass

    if data_access_levels:
        data_access = Select2Field(
            lazy_gettext('Access Level(s)'),
            [validators.Required()],
            choices=data_access_levels['valid_access_levels'],
            default=[])
        setattr(ProjectFormExtraInputs, 'data_access', data_access)


    product = SelectField(lazy_gettext('Product'),
                          [validators.Required()], choices=[("", "")], default="")
    subproduct = SelectField(lazy_gettext('Subproduct'),
                             [validators.Required()], choices=[("", "")] , default="")

    setattr(ProjectFormExtraInputs, 'product', product)
    setattr(ProjectFormExtraInputs, 'subproduct', subproduct)

    return ProjectFormExtraInputs(form_data, obj=obj)
