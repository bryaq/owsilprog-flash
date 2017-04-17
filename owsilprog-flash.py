from __future__ import print_function
import sys
import time
import os
import serial
import argparse
import math
flasher = None
file = None
try: input = raw_input
except NameError: pass
## ---------------------- Function 0---------------------------------------------------------------------
def closeall():
  if flasher:
    flasher.close()
  if file:
    file.close()
  sys.exit(1)
  
def update_progress(progress):
  if not int(progress) % 2:
    sys.stdout.write('* [{0}] {1}%\r'.format('#'*int(progress/2)+' '*(50-int(progress/2)), int(progress)))
  else:
    sys.stdout.write('* [{0}] {1}%\r'.format('#'*int(progress/2)+'='+' '*(49-int(progress/2)), int(progress)))
  if progress == 100:
    sys.stdout.write('\n');
  sys.stdout.flush()
## ---------------------- End Function 0-----------------------------------------------------------------


## ----------- ArgumentParser ---------------------------------------------------------------------------
VERSION = '0.1.1'

parser = argparse.ArgumentParser()
parser.add_argument("file", help="name of hex file to be flashed")
parser.add_argument("-p", "--port", default=None, help="connected COM Port")
parser.add_argument("-b", "--baud", default=38400, type=int, help="COM Port baudrate [default: 38400]")
args = parser.parse_args()

if not args.port:
  print('Missing PORT')
  parser.print_usage()
  sys.exit(1)
  
try:
  flasher = serial.Serial(args.port, args.baud, timeout=2)
  flasher.parity = serial.PARITY_ODD # work around pyserial issues #26, #30
  flasher.parity = serial.PARITY_NONE
  if not flasher.isOpen():
    flasher.open()
except:
  print('Cannot open port {0}'.format(args.port))
  closeall()
  
try:
  file = open(args.file, 'r')
  size_file = os.path.getsize(args.file)
except:
  print('Cannot open file {0}'.format(args.file))
  closeall()
## ----------- End ArgumentParser -----------------------------------------------------------------------
print('Port: {0} Baudrate: {1} file: {2}'.format(args.port, args.baud, args.file))
flasher.read(10)
flasher.write('t'.encode())
flasher.flush()
response = flasher.read(5)
print(response.decode())
if response.find('tok'.encode()) != -1:
  print('Port {0} Connected\nInitialize...'.format(args.port))
  flasher.write('rid'.encode())
  flasher.flush()
  response = flasher.read(20)
  i = response.find('dok'.encode())
  device_id = response[i+3:i+5].decode()
  sys.stdout.write('Device ID: 0x{0}\nConfirm to Flash {1} byte [y/n]: '.format(device_id, size_file))
 
  response = input()
 
  if response.lower() == 'y':
    
    # Erase process
    print('\nErase...')
    flasher.write('e'.encode())
    flasher.flush()
    isOK = False
    i = 0
    while not isOK:
      b = flasher.read(1)
      if b == 'o':
        i = 1
      if b == 'k' and i == 1:
        isOK = True
    flasher.read(2)
    
    # Flash process
    print('\nFlashing...')
    sendByte = 0
    update_progress(0)
    for line in file:
      line = line.strip()
      sendByte = sendByte + len(line)
      if line[0:3] != ':00':
        flasher.write(('bw'+line.strip()).encode())
        flasher.flush()
      flasher.read(len(line) + 6)
      update_progress(sendByte*100/size_file)
    update_progress(100)
    
    # reset serial IO
    flasher.flush()
    flasher.read(10)
    
    # verify process
    print('\nVerify...')
    sendByte = 0
    update_progress(0)
    file.seek(0)
    for line in file:
      line = line.strip()
      sendByte = sendByte + len(line)
      if line[0:3] != ':00':
        flasher.write(('br'+line[0:7]).encode())
        flasher.flush()
        response = flasher.read(11 + len(line))
        if response[9:11] != 'ok' or response[11:end-2] != line:
          print('error')
          closeall();
      update_progress(sendByte*100/size_file)
    update_progress(100)
    
    flasher.write('r'.encode())
    flasher.flush()
    flasher.read(5)
    print('\nSuccess\n[press any key to exit]')
    response = input()
else:
  print('Port {0} Error'.format(args.port))
closeall()
