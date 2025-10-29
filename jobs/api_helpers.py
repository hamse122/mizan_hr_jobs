"""
API helper functions for consistent error handling and response formatting.
"""

from django.http import JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


def api_success(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data (dict, list, etc.)
        message: Success message
        status_code: HTTP status code
    
    Returns:
        JsonResponse with standardized format
    """
    response_data = {
        'success': True,
        'message': message,
        'data': data or {}
    }
    return JsonResponse(response_data, status=status_code)


def api_error(message="An error occurred", errors=None, status_code=400):
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: List of detailed errors (optional)
        status_code: HTTP status code
    
    Returns:
        JsonResponse with error format
    """
    response_data = {
        'success': False,
        'message': message,
        'errors': errors or []
    }
    return JsonResponse(response_data, status=status_code)


def handle_api_exceptions(func):
    """
    Decorator to handle exceptions in API views.
    
    Usage:
        @handle_api_exceptions
        def my_api_view(request):
            # Your code here
            return api_success(data)
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ObjectDoesNotExist as e:
            logger.error(f"Object not found: {str(e)}")
            return api_error(
                message="Resource not found",
                errors=[str(e)],
                status_code=404
            )
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            errors = e.messages if hasattr(e, 'messages') else [str(e)]
            return api_error(
                message="Validation failed",
                errors=errors,
                status_code=400
            )
        except PermissionError as e:
            logger.error(f"Permission denied: {str(e)}")
            return api_error(
                message="Permission denied",
                errors=[str(e)],
                status_code=403
            )
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            return api_error(
                message="An unexpected error occurred",
                errors=["Please try again later"],
                status_code=500
            )
    return wrapper


def validate_api_params(request, required_params=None, optional_params=None):
    """
    Validate API request parameters.
    
    Args:
        request: Django request object
        required_params: List of required parameter names
        optional_params: Dict of optional params with default values
    
    Returns:
        tuple: (is_valid, data_dict, error_response)
    """
    required_params = required_params or []
    optional_params = optional_params or {}
    
    data = {}
    errors = []
    
    # Check required parameters
    for param in required_params:
        value = request.GET.get(param) or request.POST.get(param)
        if not value:
            errors.append(f"Missing required parameter: {param}")
        else:
            data[param] = value
    
    # Add optional parameters with defaults
    for param, default_value in optional_params.items():
        value = request.GET.get(param) or request.POST.get(param)
        data[param] = value if value is not None else default_value
    
    if errors:
        return False, None, api_error(
            message="Invalid request parameters",
            errors=errors,
            status_code=400
        )
    
    return True, data, None


def paginate_queryset(queryset, page_number, page_size=20):
    """
    Paginate a queryset and return paginated data with metadata.
    
    Args:
        queryset: Django queryset
        page_number: Page number (1-indexed)
        page_size: Items per page
    
    Returns:
        dict: Pagination metadata and results
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(queryset, page_size)
    total_items = paginator.count
    total_pages = paginator.num_pages
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
        page_number = 1
    except EmptyPage:
        page_obj = paginator.page(total_pages)
        page_number = total_pages
    
    return {
        'items': list(page_obj.object_list),
        'pagination': {
            'current_page': page_number,
            'total_pages': total_pages,
            'total_items': total_items,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    }

