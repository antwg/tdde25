
class A:

    @classmethod
    def stf(cls):
        print("stf: A")

    @classmethod
    def cls(cls):
        print("cls:", __class__)  # Where executed

    @classmethod
    def slf(cls):
        print("slf:", cls.__class__)

    @classmethod
    def nme(cls):
        print("nme:", cls)  # Class executing


class B(A):

    @classmethod
    def stf(cls):
        print("stf: B")

    @classmethod
    def cls(cls):
        print("cls:", __class__)

    @classmethod
    def nme(cls):
        print("nme:", cls)


class C(A):

    @classmethod
    def stf(cls):
        print("stf: C")


for cls in [A, B, C]:
    print("_"*5, cls.__name__, "_"*5)
    cls.stf()
    cls.nme()
    cls.cls()
    cls.slf()


