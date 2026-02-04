def main():
    try:
        a = float(input("Enter first number: "))
        b = float(input("Enter second number: "))
    except ValueError:
        print("Please enter valid numbers.")
        return
    print(f"{a} + {b} = {a + b}")


if __name__ == "__main__":
    main()
