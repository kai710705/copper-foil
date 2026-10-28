class DomainError(Exception):
    def __init__(self, message, code='VALIDATION', status=400):
        super().__init__(message)
        self.code = code
        self.status = status


def required_text(value, label, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise DomainError(f'{label}不得空白且最多 {maximum} 字元')
    return value.strip()
