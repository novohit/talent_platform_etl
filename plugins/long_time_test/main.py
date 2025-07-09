import time

def long_time_test():
    print("long_time_test")
    for i in range(100):
        print(f"long_time_test {i}")
        time.sleep(2)
    print("long_time_test end")

if __name__ == "__main__":
    long_time_test()