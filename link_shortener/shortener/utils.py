import string
import random

def generate_code():
    chars = string.ascii_letters + string.digits 
    return ''.join(random.choice(chars) for _ in range(6))
print(generate_code())