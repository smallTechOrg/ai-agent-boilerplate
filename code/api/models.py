

from http import HTTPStatus

from flask import jsonify


class APIResponse:
    def __init__(self, validation_response=None, data=None):
        self.validation_response = validation_response 
        self.data = data
    
    def response(self, http_status=None):
        if http_status == HTTPStatus.BAD_REQUEST:
            return jsonify({
                'success': self.validation_response.is_valid,
                'error': self.validation_response.message}), http_status
        elif http_status == HTTPStatus.OK:
            return jsonify({
                'success': True
                } | self.data), http_status
        else:
            return jsonify({
            'success': False,
            'error': "Sorry, something went wrong. Please try again later."}), http_status
        

class ValidationResponse:
    def __init__(self, is_valid, message=None, data=None):
        self.is_valid = is_valid 
        self.message = message
        self.data = data

    def is_valid(self):
        return self.is_valid