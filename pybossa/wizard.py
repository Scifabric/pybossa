from flask import url_for


class Wizard(object):
    def __init__(self, project, wizard_steps, request):
        self.project = project
        self.wizard_steps = wizard_steps
        self.request = request
        self.check_options = {
            'project_exist': self.project_exist,
            'not_project_exist': self.not_project_exist,
            'ext_config': self.ext_config,
            'tasks_amount': self.tasks_amount,
            'task_presenter': self.task_presenter,
            'project_publish': self.project_publish,
            'not_project_publish': self.not_project_publish
        }

    # Checks
    def project_exist(self):
        return self.project is not None

    def not_project_exist(self):
        return self.project is None

    def get_nested_keys(self, nested_keys):
        keys = nested_keys.split('.')
        value = self.project
        for key in keys:
            value = value.get(key)
            if value is None or value == '':
                break
        return value

    def ext_config(self):
        if self.not_project_exist():
            return False
        attrs_values = {}
        attrs = self.wizard_steps['ext_config']['config_for_checks']['attrs']
        for key in attrs.keys():
            value = self.get_nested_keys(attrs.get(key))
            value = value is not None and value != ''
            attrs_values[key] = value

        condition = self.wizard_steps['ext_config']['config_for_checks']['condition']

        and_result = []
        for c_name in condition['and']:
            and_result.append(attrs_values[c_name])

        or_result = []
        for c_name in condition['or']:
            or_result.append(attrs_values[c_name])

        return all(and_result) and any(or_result)

    def tasks_amount(self):
        if self.not_project_exist():
            return False
        return self.project['n_tasks'] > 0

    def task_presenter(self):
        if self.not_project_exist():
            return False

        task_presenter = False
        if 'task_presenter' in self.project['info']:
            task_presenter = self.project['info']['task_presenter'] != '' and self.project['info']['task_presenter'] is not None

        return task_presenter

    def project_publish(self):
        if self.not_project_exist():
            return False
        return self.project['published']

    def not_project_publish(self):
        if self.not_project_exist():
            return False
        return not self.project['published']

    def wizard_check_switch(self, check_name):
        func = self.check_options.get(check_name, lambda: False)
        return func()

    def run_checks(self, conditions):
        if 'always' in conditions:
            return conditions['always']

        and_result = []
        or_result = []

        for condition in conditions['and']:
            and_result.append(self.wizard_check_switch(condition))

        for condition in conditions['or']:
            or_result.append(self.wizard_check_switch(condition))
        return all(and_result) or any(or_result)

    def get_href(self, href_config, enable):
        if not enable:
            return ''

        if 'published' in href_config['args']:
            return url_for(href_config['url_for'], short_name=self.project['short_name'], published=self.project['id'])

        if 'short_name' in href_config['args']:
            return url_for(href_config['url_for'], short_name=self.project['short_name'])

        return url_for(href_config['url_for'])

    def get_step(self, step):
        if not self.run_checks(step['visible_checks']):
            return None

        enable = self.run_checks(step['enable_checks'])
        href = self.get_href(step['href'], enable)
        active = (self.request['url'].endswith(href) and href != '') or self.request['path'].endswith(href) and href != ''

        return dict(href=href,
                    title=step['title'],
                    icon=step['icon'],
                    done=self.run_checks(step['done_checks']),
                    enable=enable,
                    active=active)

    def get_wizard_list(self):
        current_wizard = []
        for key, step in self.wizard_steps.items():
            step = self.get_step(step)
            if step is not None:
                current_wizard.append(step)
        return current_wizard


