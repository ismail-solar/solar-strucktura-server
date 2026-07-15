import uuid
from datetime import datetime
import random
import string

def generate_invoice_number():
    year = datetime.now().year
    # Generate a 10-character random alphanumeric string
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    # Solar-themed prefix
    return f"INV-SLR-{year}-{random_str}"