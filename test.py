print("Mini game")

n = int(input("Write a number: "))

print("Четные числа: ")
for i in range (1, n+1):
    if i % 2 == 0:
        print(i)
print("Нечетные числа: ")
for i in range(1,n+1):
    if i % 2 != 0:
        print(i)
print("Числа делящиеся на 3: ")
for i in range(1,n+1):
    if i % 3 == 0:
        print(i)
print("Числа делящиеся на 5: ")
for i in range(1,n+1):
    if i % 5 == 0:
        print
