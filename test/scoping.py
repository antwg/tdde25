

text = "HEJ!"


class A:
    text = "HEJ från A!"

    def yell(self):
        text = "TEMP!"
        print(self.text)
        print(text)


a = A()

a.yell()
