"""Example Python file with intentional naming violations."""

# Constants should be UPPER_SNAKE_CASE
MaxUsers = 100  # Violation: should be MAX_USERS
MIN_TEMP = 0  # Correct

# Classes should be PascalCase
class user_manager:  # Violation: should be UserManager
    pass

class DataProcessor:  # Correct
    pass

# Functions should be snake_case
def ProcessData():  # Violation: should be process_data
    pass

def fetch_user_data():  # Correct
    pass

def _private_helper():  # Correct: private with underscore
    pass

def anotherPrivateFunction():  # Violation: camelCase in Python
    pass

# Variables should be snake_case
UserCount = 0  # Violation: should be user_count
total_items = 0  # Correct

# Module-level code
result = fetch_user_data()

