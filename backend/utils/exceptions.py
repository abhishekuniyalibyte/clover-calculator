from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Customize the response format
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': '',
            'errors': {}
        }

        # Handle validation errors
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
            else:
                custom_response_data['errors'] = response.data
                custom_response_data['message'] = 'Validation error'
        elif isinstance(response.data, list):
            custom_response_data['message'] = response.data[0] if response.data else 'An error occurred'
        else:
            custom_response_data['message'] = str(response.data)

        response.data = custom_response_data

    return response
