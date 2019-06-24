import sys

def Main():
    print(sys.platform)
    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
