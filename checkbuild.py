import os
import sys

def Main():
    print(sys.platform)
    print(os.listdir(os.path.join('dist','main')))
    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
