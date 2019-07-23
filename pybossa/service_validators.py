import regex

whitelist_regex = regex.compile(ur"[^a-zA-Z0-9\.\u00BC-\u00BE\u2150-\u215E\s]")


class ServiceValidators(object):
    def __init__(self, service):
        self.service = service

    # Validators
    def is_valid_query(self, service_request, payload):
        service_data = payload.get('data')
        query = service_data[service_request].get('query', None)
        matches = whitelist_regex.search(query)
        if len(query) < 20 and not matches:
            return True

        return False

    def is_valid_context(self, service_request, payload):
        service_data = payload.get('data')
        context = service_data[service_request].get('context', None)
        return context in self.service['context']

    def run_validators(self, service_request, payload):
        validation_results = []
        for validation in self.service['validators']:
            validation_results.append(getattr(self, validation)(service_request, payload))
        return all(validation_results)
