from unidecode import unidecode
import re


def remove_accents(s):
    accent_map = {
        ord(accent): unidecode(accent)
        for accent in set(s)
        if accent != unidecode(accent)
    }

    return s.translate(accent_map)


def extract_numbers(string):
    numbers = re.findall("\d+", string)
    return "".join(numbers)


def extract_letters(string):
    letters = re.findall("[A-Za-z]+", string)
    return "".join(letters)

    
