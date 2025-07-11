ls = [2, 5, 11, 7, 3, 8]

def check_prime(ls):
    for i in ls:
        if i > 1:
            for j in range(2, i):
                if i % j == 0:
                    print('Not prime number:', i)
                    break
            else:
                # This else belongs to the for loop, runs only if no break
                print('Prime number:', i)
        else:
            print('Not prime number:', i)

check_prime(ls)

