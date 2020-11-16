
class A():

    a = "A"

    def __init__(self):
        self.b = "B"


print(dir(A().__dir__))
print(A.__dict__)
print(A().__dict__)
