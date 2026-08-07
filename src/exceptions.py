"""
Custom exceptions for the AI ETR Predictor SMKKJ project.

Using dedicated exception types (instead of letting raw `FileNotFoundError`,
`KeyError`, etc. bubble up) lets `app.py` catch data/model problems
specifically and show a friendly Streamlit message, while anything truly
unexpected still surfaces as a normal traceback in the logs.
"""


class ETRPredictorError(Exception):
    """Base class for all project-specific errors."""


class DataFileNotFoundError(ETRPredictorError):
    """Raised when a required raw data file is missing from data/raw."""


class DataParsingError(ETRPredictorError):
    """Raised when a workbook/sheet does not match the expected layout."""


class ModelNotTrainedError(ETRPredictorError):
    """Raised when predict()/save() is called before the model is fitted."""


class InsufficientDataError(ETRPredictorError):
    """Raised when there isn't enough data to safely fit or evaluate a model."""


class AuthenticationError(ETRPredictorError):
    """Raised when login credentials are invalid or the account is inactive."""
