#-*- coding: utf8 -*-
from pybossa.service_validators import ServiceValidators
from default import Test, with_context


class ServiceValidatorTestHelper(Test):

    def get_service(self):
        return {
            'headers': {'CCRT-test': 'test'},
            'requests': ['queryTest'],
            'context': ['test_context'],
            'validators': ['is_valid_query', 'is_valid_context']}

    def get_valid_payload(self):
        return {
            'data': {'queryTest': {
                'context': "test_context",
                'query': u"½.½ uuujfA 11109",
                'maxresults': 10}}}

    def get_invalid_payload(self):
        return {
            'data': {
                'queryTest': {
                    'context': "invalid_context",
                    'query': u"@_hhfu",
                    'maxresults': 10}}}


class TestServiceValidator(ServiceValidatorTestHelper):

    @with_context
    def test_is_valid_query(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_valid_payload())
        assert service_validator.is_valid_query()

    @with_context
    def test_is_valid_query_with_invalid_query(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_invalid_payload())
        assert not service_validator.is_valid_query()

    @with_context
    def test_is_valid_context(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_valid_payload())
        assert service_validator.is_valid_context()

    @with_context
    def test_is_valid_context_with_invalid_context(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_invalid_payload())
        assert not service_validator.is_valid_context()

    @with_context
    def test_run_validators_with_valid_payload(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_valid_payload())
        assert service_validator.run_validators()

    @with_context
    def test_run_validators_with_invalid_payload(self):
        service_validator = ServiceValidators(self.get_service(), 'queryTest', self.get_invalid_payload())
        assert not service_validator.run_validators()




