
"""
A class can reference to another class, just as that class can reference the
first, but only if the two exists in the sam space.
"""


class B:

    def out(self):
        print("B - Out")
        if isinstance(self, A):
            self.admit()


class A(B):

    def admit(self):
        print("But im really", self.__class__)


A().out()
