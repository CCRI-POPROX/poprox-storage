from botocore.exceptions import ClientError


class PoproxUtilitiesException(Exception):
    """Base class for all Poprox Utilities exceptions. Don't use directly."""


class PoproxAwsUtilitiesException(PoproxUtilitiesException):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        if isinstance(errors, ClientError):
            self.errors = {
                "code": errors.response["ResponseMetadata"]["HTTPStatusCode"],
                "message": errors.response["Error"]["Message"],
                "requestId": errors.response["ResponseMetadata"]["RequestId"],
            }
        else:
            self.errors = errors

    def __str__(self):
        return self.message

    def __repr__(self):
        return {"message": self.message, "errors": self.errors}.__repr__()
