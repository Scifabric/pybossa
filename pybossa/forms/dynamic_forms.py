from flask_babel import lazy_gettext
from flask_wtf import FlaskForm as Form
from wtforms import SelectField, validators, TextField, BooleanField
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

def dynamic_project_form(class_type, form_data, data_access_levels, products=None, obj=None):

    class ProjectFormExtraInputs(class_type):
        def __init__(self, *args, **kwargs):
            class_type.__init__(self, *args, **kwargs)
            set_product_subproduct_choices(self, products)
        pass

    if data_access_levels:
        data_access = Select2Field(
            lazy_gettext('Access Level(s)'),
            [validators.Required()],
            choices=data_access_levels['valid_access_levels'],
            default=[])
        ProjectFormExtraInputs.data_access = data_access
        ProjectFormExtraInputs.amp_store = BooleanField(
            lazy_gettext('Opt in to store annotations on Annotation Management Platform'))
        ProjectFormExtraInputs.amp_pvf = TextField(
            lazy_gettext('Annotation Store PVF'),
            [validators.Regexp('^([A-Z]{3,4}\s\d+)?$')]) #[validators.Regexp('^$|[A-Z]\s\d')])


    return ProjectFormExtraInputs(form_data, obj=obj)

def set_product_subproduct_choices(form, config_products):
    config_products = config_products or {}
    products = list(config_products.keys())
    choices = [("", "")]
    form.product.choices = choices + [(p, p) for p in products]
    product = form.product.data
    if product:
        subproducts = config_products.get(product, [])
        choices += [(sp, sp) for sp in subproducts]
    form.subproduct.choices = choices
