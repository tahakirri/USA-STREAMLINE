def is_fancy_number(phone_number):
    """
    Determine if a phone number is 'fancy' based on various patterns
    
    Args:
        phone_number (str): The phone number to check
    
    Returns:
        dict: A dictionary with fancy status and reasoning
    """
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone_number)
    
    # Check if shorter than 10 digits or not a valid phone number
    if len(digits) < 10:
        return {
            "is_fancy": False,
            "reason": "Invalid phone number length"
        }
    
    # More comprehensive fancy patterns to check
    fancy_patterns = [
        # Strict repeating digits - at least 4 consecutive identical digits
        (r'(\d)\1{3,}', "Has four or more consecutive repeating digits"),
        
        # Sequential patterns (including non-continuous)
        (lambda x: all(int(x[i]) + 1 == int(x[i+1]) for i in range(len(x)-1)), "Contains perfect ascending sequence"),
        (lambda x: all(int(x[i]) - 1 == int(x[i+1]) for i in range(len(x)-1)), "Contains perfect descending sequence"),
        
        # True palindromes (using full number)
        (lambda x: x == x[::-1] and len(x) >= 10, "Is a full palindrome number"),
        
        # Rare sequential patterns
        (r'101010|123123|234234', "Contains rare repeating sequential pattern"),
        
        # Super minimal unique digits
        (lambda x: len(set(x)) <= 1, "Consists of single unique digit"),
        
        # Extremely lucky/symbolic numbers
        (r'888888|666666|999999', "Contains extremely lucky/symbolic number"),
    ]
    
    # Counter to track how many patterns match
    pattern_matches = 0
    matched_reasons = []
    
    for pattern in fancy_patterns:
        # Handle both regex and lambda pattern checks
        try:
            if isinstance(pattern[0], str):
                match = re.search(pattern[0], digits)
                if match:
                    pattern_matches += 1
                    matched_reasons.append(pattern[1])
            elif callable(pattern[0]):
                if pattern[0](digits):
                    pattern_matches += 1
                    matched_reasons.append(pattern[1])
        except:
            pass
    
    # Only consider very fancy if multiple patterns match
    if pattern_matches >= 1:
        return {
            "is_fancy": True,
            "reason": " and ".join(matched_reasons)
        }
    
    return {
        "is_fancy": False,
        "reason": "Standard phone number"
    }
