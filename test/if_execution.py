
def true():
    print("first: HIT")
    return True


def false():
    print("second: HIT")
    return True


if false() and true():
    print("false and true: hit")
else:
    print("false and true: miss")

if true() and false():
    print("true and false: hit")
else:
    print("true and false: miss")


if false() and false():
    print("false and false: hit")
else:
    print("true and true: miss")


if true() and true():
    print("true and true: hit")
else:
    print("true and true: miss")

