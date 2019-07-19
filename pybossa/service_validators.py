import regex


class ServiceValidators(object):
    def __init__(self, service, service_request, payload):
        self.service = service
        self.service_request = service_request
        self.payload = payload
        self.validators = {
            'is_valid_query': self.is_valid_query,
            'is_valid_context': self.is_valid_context
        }

    # Validators
    def is_valid_query(self):
        service_data = self.payload.get('data')
        whitelist_regex = regex.compile(ur"[^a-zAz0-9\.\u00BC-\u00BE\u2150-\u215E\s]")
        query = service_data[self.service_request].get('query', None)
        matches = whitelist_regex.search(query)
        if len(query) < 20 and not matches:
            return True

        return False

    def is_valid_context(self):
        service_data = self.payload.get('data')
        context = service_data[self.service_request].get('context', None)
        return context in self.service['context']

    def validator_switch(self, validator_name):
        func = self.validators.get(validator_name, lambda: False)
        return func()

    def run_validators(self):
        validation_results = []
        for validation in self.service['validators']:
            validation_results.append(self.validator_switch(validation))
        return all(validation_results)
