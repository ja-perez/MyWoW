# Data Exceptions
class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class InvalidDataError(Exception):
    """Raised when a prediction object is initialized with invalid data"""
    pass

# Input Exceptions
class InvalidInputError(Exception):
    """Raised when input is invalid."""
    pass

class ValidateInputError(Exception):
    """Raised when input validation fails."""
    pass

class QuitInputError(Exception):
    """Raised when user quits the input process."""
    pass

class CancelInputError(Exception):
    """Raised when input is cancelled."""
    pass

class RefreshInputError(Exception):
    """Raised when input process is refreshed."""
    pass

# Menu Exceptions
class QuitMenuError(Exception):
    """Raised when user quits the program."""
    pass

class CancelMenuError(Exception):
    """Raised when the menu is cancelled"""
    pass

class RefreshMenuError(Exception):
    """Raised when the menu is refreshed"""