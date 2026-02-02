from datetime import datetime

def get_current_time():
    """Get the current date and time.
    
    Returns:
        str: Current date and time in a readable format
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def add_numbers(a, b):
    """Add two numbers together.
    
    Args:
        a (int or float): First number to add
        b (int or float): Second number to add
        
    Returns:
        int or float: Sum of the two numbers
    """
    return a + b