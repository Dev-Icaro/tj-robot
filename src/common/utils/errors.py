class ValidationResult:
    def __init__(self):
        self.errors = []

    def to_array(self):
        return self.errors

    def add_error(self, error):
        self.errors.append()

    def is_empty(self):
        return len(self.errors) <= 0
