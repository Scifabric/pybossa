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

def dynamic_project_form(class_type, form_data, data_access_levels, products=None, data_classes=None, obj=None):

    class ProjectFormExtraInputs(class_type):
        def __init__(self, *args, **kwargs):
            class_type.__init__(self, *args, **kwargs)
            set_product_subproduct_choices(self, products)
            set_data_classification_choices(self, data_classes)
        pass

    if data_access_levels:
        ProjectFormExtraInputs.amp_store = BooleanField(
            lazy_gettext('Opt in to store annotations on Annotation Management Platform'))
        ProjectFormExtraInputs.amp_pvf = TextField(
            lazy_gettext('Annotation Store PVF'),
            [validators.Regexp('^([A-Z]{3,4}\s\d+)?$')]) #[validators.Regexp('^$|[A-Z]\s\d')])

    generate_form = ProjectFormExtraInputs(form_data, obj=obj)
    if data_access_levels and not form_data:
        generate_form.amp_store.data = bool(not obj or obj.amp_store)
    return generate_form

def dynamic_clone_project_form(class_type, form_data, data_access_levels, data_classes=None, obj=None):

    class ProjectCloneFormExtraInputs(class_type):
        def __init__(self, *args, **kwargs):
            class_type.__init__(self, *args, **kwargs)
            set_data_classification_choices(self, data_classes)
        pass

    if data_access_levels:
        ProjectCloneFormExtraInputs.copy_users = BooleanField(
            lazy_gettext('Keep same list of assigned users'))

    return ProjectCloneFormExtraInputs(form_data, obj=obj)

def set_product_subproduct_choices(form, config_products):
    config_products = config_products or {}
    products = list(config_products.keys())
    choices = [("", "")]
    form.product.choices = sorted(choices + [(p, p) for p in products])
    product = form.product.data
    if product:
        subproducts = config_products.get(product, [])
        choices += [(sp, sp) for sp in subproducts]
    form.subproduct.choices = choices

def set_data_classification_choices(form, data_classes):
    choices = data_classes or [('', '', dict(disabled='disabled'))]
    form.input_data_class.choices = choices
    form.output_data_class.choices = choices
