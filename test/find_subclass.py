
# NOTE: Link to game
# r"C:\Program Files (x86)\StarCraft II\Versions\Base81433\SC2_x64.exe"

class A:
    text = 'Hello!'


class B(A):
    text = 'My'


class C(A):
    text = 'name'


class D(C):
    pass


class E(D):
    text = 'world!'


def print_all_subclass(cls):
    print(cls.text)
    for subcls in cls.__subclasses__():
        print_all_subclass(subcls)


print_all_subclass(A)



