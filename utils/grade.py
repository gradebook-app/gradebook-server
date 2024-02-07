def letter_to_number(letter):
    if letter.upper() == "A+":
        return 100
    elif letter.upper() == "A":
        return 93
    elif letter.upper() == "A-":
        return 90
    elif letter.upper() == "B+":
        return 87
    elif letter.upper() == "B":
        return 83
    elif letter.upper() == "B-":
        return 80
    elif letter.upper() == "C+":
        return 77
    elif letter.upper() == "C":
        return 73
    elif letter.upper() == "C-":
        return 70
    elif letter.upper() == "D+":
        return 67
    elif letter.upper() == "D":
        return 65
    elif letter.upper() == "D-":
        return 65
    elif letter.upper() == "F":
        return 64
    else:
        return 64


def number_to_letter(number):
    if number >= 98:
        return "A+"
    elif number >= 93:
        return "A"
    elif number >= 90:
        return "A-"
    elif number >= 87:
        return "B+"
    elif number >= 83:
        return "B"
    elif number >= 80:
        return "B-"
    elif number >= 77:
        return "C+"
    elif number >= 73:
        return "C"
    elif number >= 70:
        return "C"
    elif number >= 67:
        return "D+"
    elif number >= 65:
        return "D"
    else:
        return "F"
