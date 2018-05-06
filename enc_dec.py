import os
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import random
import string
import binascii

key = ''

def encrypt(key, filename, new_filename):
	# reading chunks from the file
	chunksize = 64*1024
	outputFile = new_filename
	filesize = str(os.path.getsize(filename)).zfill(16)
	#iv used to randomize and produce distinct ciphertext
	IV = Random.new().read(16)

	encryptor = AES.new(key, AES.MODE_CBC, IV)

	with open(filename, 'rb') as infile:
		with open(outputFile, 'wb') as outfile:
			outfile.write(filesize.encode('utf-8'))
			outfile.write(IV)
			
			while True:
				chunk = infile.read(chunksize)
				
				if len(chunk) == 0:
					break
				elif len(chunk) % 16 != 0:
					# ' ' to pad chuncks
					chunk += b' ' * (16 - (len(chunk) % 16))

				outfile.write(encryptor.encrypt(chunk))
	return outputFile

def decrypt(key, filename, new_filename):
	chunksize = 64*1024
	outputFile = new_filename
	
	with open(filename, 'rb') as infile:
		filesize = int(infile.read(16))
		IV = infile.read(16)

		decryptor = AES.new(key, AES.MODE_CBC, IV)

		with open(outputFile, 'wb') as outfile:
			while True:
				chunk = infile.read(chunksize)

				if len(chunk) == 0:
					break

				outfile.write(decryptor.decrypt(chunk))
			outfile.truncate(filesize)
	return outputFile

# Key ...  make it static as it must be on my computer 
def gen_Key():
	key = "hello"
	#key =''.join(random.sample(string.ascii_lowercase, 10))
	return key

def getKey(key):
	hasher = SHA256.new(key.encode('utf-8'))
	return hasher.digest()

def encryptMain(filename, new_filename):
	global key
	key = gen_Key()
	encrypt(getKey(key), filename)

def decryptMain(filename, new_filename):
	global key
	key = gen_Key()
	decrypt(getKey(key), filename)

#def Main():
#	choice = input("Would you like to (E)ncrypt or (D)ecrypt?: ")
#	global key
#	key = gen_Key()
#	if choice == 'E':
#		filename = input("File to encrypt: ")
#		encrypt(getKey(key), filename)
#		print("Done.")
#	elif choice == 'D':
#		filename = input("File to decrypt: ")
#		decrypt(getKey(key), filename)
#		print("Done.")
#	else:
#		print("No Option selected, closing...")

if __name__ == '__main__':
	Main()














