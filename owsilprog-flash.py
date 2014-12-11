import sys
import time
import os
import serial
import argparse
import math
flasher = None
file = None
isPython2 = sys.hexversion < 0x3000000
## ---------------------- Function 0---------------------------------------------------------------------
def closeall():
  if flasher:
    flasher.close()
  if file:
    file.close()
  sys.exit(1)
  
def update_progress(progress):
  if not progress % 2:
    sys.stdout.write('* [{0}] {1}%\r'.format('#'*(progress/2)+' '*(50-progress/2), progress))
  else:
    sys.stdout.write('* [{0}] {1}%\r'.format('#'*(progress/2)+'='+' '*(49-progress/2), progress))
  if progress == 100:
    sys.stdout.write('\n');
  sys.stdout.flush()
## ---------------------- End Function 0-----------------------------------------------------------------


## ----------- ArgumentParser ---------------------------------------------------------------------------
VERSION = '0.1.0'

parser = argparse.ArgumentParser()
parser.add_argument("file", help="name of hex file to be flashed")
parser.add_argument("-p", "--port", default=None, help="connected COM Port")
parser.add_argument("-b", "--baud", default=38400, type=int, help="COM Port baudrate [default: 38400]")
args = parser.parse_args()

if not args.port:
  print 'Missing PORT'
  parser.print_usage()
  sys.exit(1)
  
try:
  flasher = serial.Serial(args.port, args.baud, timeout=2)
  if not flasher.isOpen():
    flasher.open()
except:
  print 'Cannot open port {0}'.format(args.port)
  closeall()
  
try:
  file = open(args.file, 'r')
  size_file = os.path.getsize(args.file)
except:
  print 'Cannot open file {0}'.format(args.file)
  closeall()
## ----------- End ArgumentParser -----------------------------------------------------------------------
print 'Port: {0} Baudrate: {1} file: {2}'.format(args.port, args.baud, args.file)
flasher.read(10)
flasher.write('t')
flasher.flush()
response = flasher.read(5)
print response
if response.find('tok') != -1:
  print 'Port {0} Connected\nInitialize...'.format(args.port)
  flasher.write('rid')
  response = flasher.read(20)
  i = response.find('dok')
  device_id = response[i+3:i+5]
  sys.stdout.write('Device ID: 0x{0}\nConfirm to Flash {1} byte [y/n]: '.format(device_id, size_file))
  
  if isPython2:
    response = raw_input()
  else:
    response = input()
  if response.lower() == 'y':
    print '\nFlashing...'
    sendByte = 0
    update_progress(0)
    for line in file:
      line = line.strip()
      sendByte = sendByte + len(line)
      if line[0:3] != ':00':
        flasher.write('bw'+line.strip())
        flasher.flush()
      flasher.read(len(line) + 6)
      update_progress(sendByte*100/size_file)
    update_progress(100)
    
    print '\nVerify...'
    sendByte = 0
    update_progress(0)
    for line in file:
      line = line.strip()
      sendByte = sendByte + len(line)
      if line[0:3] != ':00':
        flasher.write('br'+line[0:7])
        flasher.flush()
        response = flasher.read(11 + len(line))
        if response[9:11] != 'ok' or response[11:end-2] != line:
          print 'error'
          closeall();
      update_progress(sendByte*100/size_file)
    update_progress(100)
    
    flasher.write('r')
    flasher.flush()
    flasher.read(5)
    print '\nSuccess\n[press any key to exit]'
    if isPython2:
      response = raw_input()
    else:
      response = input()
else:
  print 'Port {0} Error'.format(args.port)
closeall()