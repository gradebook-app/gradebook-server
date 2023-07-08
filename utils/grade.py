def grade(letter):
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
