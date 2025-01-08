from dataclasses import dataclass
from typing import List, Optional, Any
from google.ads.googleads.errors import GoogleAdsException


@dataclass
class GoogleAdsErrorDetail:
    type_: str
    value: str


@dataclass
class GoogleAdsError:
    error_request_id: str
    error_code: str
    error_message: str
    fields: List[str]
    class_name: str
    id: str
    class_id: Optional[str] = None
    details: List[GoogleAdsErrorDetail] = None
    trigger: Optional[str] = None
    location: Optional[Any] = None


class GoogleAdsErrorHandler:
    """Centralized error handling for Google Ads API interactions."""

    @staticmethod
    def create_error(
        ex: GoogleAdsException, class_name: str, id: str, class_id: Optional[str] = None
    ) -> GoogleAdsError:
        """Create a standardized error object from a Google Ads exception."""
        error_message = GoogleAdsErrorHandler._extract_error_message(ex)
        fields = GoogleAdsErrorHandler._extract_error_fields(ex)
        details = GoogleAdsErrorHandler._extract_error_details(ex)
        return GoogleAdsError(
            error_request_id=ex.request_id,
            error_code=ex.error.code().name,
            error_message=error_message,
            fields=fields,
            class_name=class_name,
            id=id,
            class_id=class_id,
            details=details,
            trigger=GoogleAdsErrorHandler._extract_trigger(ex),
            location=GoogleAdsErrorHandler._extract_location(ex),
        )

    @staticmethod
    def _extract_error_message(ex: GoogleAdsException) -> str:
        """Extract the most relevant error message from the exception."""
        if hasattr(ex.error, "policy_violation_details"):
            return ex.error.policy_violation_details.external_policy_name

        if hasattr(ex.error, "message") and hasattr(ex.error, "details"):
            return ex.error.details

        return getattr(ex.error, "message", "") or getattr(ex.error, "details", "")

    @staticmethod
    def _extract_error_fields(ex: GoogleAdsException) -> List[str]:
        """Extract field names from error location."""
        fields = []
        for error in ex.failure.errors:
            if error.location:
                fields.extend(element.field_name for element in error.location.field_path_elements)
        return fields

    @staticmethod
    def _extract_error_details(ex: GoogleAdsException) -> List[GoogleAdsErrorDetail]:
        """Extract detailed error information."""
        details = []
        try:
            error = ex.failure.errors[0]
            if hasattr(error, "details"):
                # Handle the case where details is not iterable
                detail_dict = error.details.to_dict()
                for key, value in detail_dict.items():
                    details.append(GoogleAdsErrorDetail(type_=key, value=str(value)))
        except (AttributeError, IndexError):
            pass
        return details

    @staticmethod
    def _extract_trigger(ex: GoogleAdsException) -> Optional[str]:
        """Extract trigger information from the error."""
        try:
            return ex.failure.errors[0].trigger.string_value
        except (AttributeError, IndexError):
            return None

    @staticmethod
    def _extract_location(ex: GoogleAdsException) -> Optional[Any]:
        """Extract location information from the error."""
        try:
            return ex.failure.errors[0].location.field_path_elements
        except (AttributeError, IndexError):
            return None
