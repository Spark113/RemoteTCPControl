__author__ = 'Yossi'

# 2.6  client server October 2021
import socket, random, traceback
import time, threading, os, datetime
from contextlib import nullcontext
from sys import exception

from datetime import datetime

from tcp_by_size import send_with_size,recv_by_size
import pyautogui
import glob
import os
import shutil
import subprocess
all_to_die = False  # global
counk=1024# global

def logtcp(dir,tid, byte_data):
	"""
	log direction, tid and all TCP byte array data
	return: void
	"""
	if dir == 'sent':
		print(f'{tid} S LOG:Sent     >>> {byte_data}')
	else:
		print(f'{tid} S LOG:Recieved <<< {byte_data}')


def get_screen_shot(file_name,sock):
	try:
		image = pyautogui.screenshot()
		image.save(file_name)
		send_file(file_name,sock)
		#replay='ENDF'
		#send_with_size(sock,replay.encode())
	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))


def send_file(file_name,sock):
	global counk
	try:
		reply = 'SNDF'
		send_with_size(sock, reply.encode('utf-8'))
		recv_by_size(sock)
		with open(file_name,'rb') as f:
			while (True):
				line = f.read(counk)
				if not line:
					break
				reply = 'CONF' +'~'
				send_with_size(sock, reply.encode('utf-8')+line)
				recv_by_size(sock)
	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))


def dir(path_name,sock):
	try:
		if not os.path.exists(path_name):
			raise FileNotFoundError('The path '+path_name+' does not exist.')
		if not os.path.isdir(path_name):
			raise NotADirectoryError('The path '+path_name+' is not a directory.')

		items = os.listdir(path_name)
		details = []
		for item in items:
			full_path = os.path.join(path_name, item)
			if os.path.isdir(full_path):
				details.append(f"{item} (Directory)")
			elif os.path.isfile(full_path):
				size = os.path.getsize(full_path)
				creation_time = datetime.fromtimestamp(os.path.getctime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
				details.append(f"{item} (File, {size} bytes, created: {creation_time})")

		return "\n".join(details)

	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))


def delete(file_name,sock):
	try:
		os.remove(file_name)
	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))


def copy_file(path_from,path_to,sock):
	try:
		shutil.copy(path_from,path_to)
	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))

def execute(path,sock):
	try:
		subprocess.call(path)
	except Exception as err:
		send_with_size(sock, ('ERRR'+str(err)).encode('utf-8'))


def get_time():
	"""return local time """
	return datetime.now().strftime('%H:%M:%S:%f')


def get_random():
	"""return random 1-10 """
	return str(random.randint(1, 10))


def get_server_name():
	"""return server name from os environment """
	return  os.environ['COMPUTERNAME']


def protocol_build_reply(request,sock):
	"""
	Application Business Logic
	function despatcher ! for each code will get to some function that handle specific request
	Handle client request and prepare the reply info
	string:return: reply
	"""
	request_code = request[:4].decode()  # Extract the first 4 characters as the request code
	request = request.decode("utf8")  # Decode the full request for further processing
	fields = request.split("~")  # Split the request into fields

	if request_code == 'GEXE':
		execute(fields[1], sock)
		reply = 'SEXE'
		return reply.encode()

	elif request_code == 'DDEL':
		delete(fields[1], sock)
		reply = 'SDEL'
		return reply.encode()

	elif request_code == 'COPY':
		copy_file(fields[1], fields[2], sock)
		reply = 'COPS'
		return reply.encode()

	elif request_code == 'GSNF':
		send_file(fields[1],sock)
		reply = 'ENDF'
		return reply.encode()

	elif request_code == 'SCRP':
		# Take a screenshot
		get_screen_shot(fields[1], sock)
		reply = 'ENDF~Screenshot taken'
		return reply.encode()

	elif request_code == 'DDIR':
		# List directory contents
		s=dir(fields[1], sock)
		reply = 'SDIR'+'~'+s
		return reply.encode()

	elif request_code == 'TIME':
		# Return server time
		reply = 'TIMR~' + get_time()
		return reply.encode()

	elif request_code == 'RAND':
		# Return a random number
		reply = 'RNDR~' + get_random()
		return reply.encode()

	elif request_code == 'WHOU':
		# Return server name
		reply = 'WHOR~' + get_server_name()
		return reply.encode()

	elif request_code == 'EXIT':
		# Terminate the connection
		reply = 'EXTR~Connection closing'
		return reply.encode()

	else:
		# Handle unsupported codes
		reply = 'ERRR~002~Code not supported'

	return reply.encode()


def handle_request(request,sock):
	"""
	Hadle client request
	tuple :return: return message to send to client and bool if to close the client socket
	"""
	try:
		request_code = request[:4]
		to_send = protocol_build_reply(request,sock)
		if request_code == b'EXIT':
			return to_send, True
	except Exception as err:
		print(traceback.format_exc())
		to_send =  b'ERRR~001~General error'
	return to_send, False


def handle_client(sock, tid , addr):
	"""
	Main client thread loop (in the server),
	:param sock: client socket
	:param tid: thread number
	:param addr: client ip + reply port
	:return: void
	"""
	global all_to_die

	finish = False
	print(f'New Client number {tid} from {addr}')
	while not finish:
		if all_to_die:
			print('will close due to main server issue')
			break
		try:
			byte_data = recv_by_size(sock)  # todo improve it to recv by message size
			if byte_data == b'':
				print ('Seems client disconnected')
				break
			logtcp('recv',tid, byte_data)

			to_send , finish = handle_request(byte_data,sock)
			if to_send != '':
				send_with_size(sock,to_send)
			if finish:
				time.sleep(1)
				break
		except socket.error as err:
			print(f'Socket Error exit client loop: err:  {err}')
			break
		except Exception as  err:
			print(f'General Error %s exit client loop: {err}')
			print(traceback.format_exc())
			break

	print(f'Client {tid} Exit')
	sock.close()


def main ():
	global  all_to_die
	"""
	main server loop
	1. accept tcp connection
	2. create thread for each connected new client
	3. wait for all threads
	4. every X clients limit will exit
	"""
	threads = []
	srv_sock = socket.socket()

	srv_sock.bind(('0.0.0.0', 1234))

	srv_sock.listen(20)

	#next line release the port
	srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	i = 1
	while True:
		print('\nMain thread: before accepting ...')
		cli_sock , addr = srv_sock.accept()
		t = threading.Thread(target = handle_client, args=(cli_sock, str(i),addr))
		t.start()
		i+=1
		threads.append(t)
		if i > 100000000:     # for tests change it to 4
			print('\nMain thread: going down for maintenance')
			break

	all_to_die = True
	print('Main thread: waiting to all clints to die')
	for t in threads:
		t.join()
	srv_sock.close()
	print( 'Bye ..')


if __name__ == '__main__':
	main()
