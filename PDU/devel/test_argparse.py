import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--aa')
parser.add_argument('-b', '--bb', nargs = '?', const = 10, default = 123)
parser.add_argument('-c', '--cc', )

op = parser.parse_args()
try:
    print 'aa = ', op.aa
except:
    print 'aa error'
try:
    print 'bb =', op.bb
except:
    print 'bb error'
try:
    print 'cc =', op.cc
except:
    print 'cc error'
