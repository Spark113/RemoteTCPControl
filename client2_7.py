__author__ = 'Yossi'
# 2.6  client server October 2021

import socket, sys,traceback
from dataclasses import field

from tcp_by_size import send_with_size,recv_by_size


def logtcp(dir, byte_data):
    """
    log direction and all TCP byte array data
    return: void
    """
    if dir == 'sent':
        print(f'C LOG:Sent     >>>{byte_data}')
    else:
        print(f'C LOG:Recieved <<<{byte_data}')


def menu():
    """
    show client menu
    return: string with selection
    """
    print('\n  1. ask for time')
    print('\n  2. ask for random')
    print('\n  3. ask for name')
    print('\n  4. notify exit')
    print('\n  5. ask for screen photo')
    print('\n  6. ask for a file ')
    print('\n  7. ask for dir')
    print('\n  8. ask to delete')
    print('\n  9. ask to copy')
    print('\n  10. ask to execute')
    print('\n  (11. some invalid data for testing)')
    return input('Input 1 - 10 > ' )

def put_in_file(sock):
    try:
        file_name = input('file place and name')
        send_with_size(sock,b'ok')
        try:
            with open(file_name, 'xb') as f:
                print('File created: '+file_name)
        except Exception as err:
            print('Error receiving file:'+str(err))
        with open(file_name, 'wb') as f:
            while True:
                data = recv_by_size(sock)
                code = data[:4]
                if (code.decode()=='ENDF'):
                    break
                elif (code.decode()=='CONF'):
                    f.write(data[5:])
                    send_with_size(sock, b"GETF")
    except Exception as err:
        print('Error receiving file:'+str(err))




def protocol_build_request(from_user):
    """
    build the request according to user selection and protocol
    return: string - msg code
    """
    if from_user == '1':
        return 'TIME'
    elif from_user == '2':
        return 'RAND'
    elif from_user == '3':
        return 'WHOU'
    elif from_user == '4':
        return 'EXIT'
    elif from_user == '5':
        return 'SCRP'+'~'+input('file path')
    elif from_user == '6':
        return 'GSNF'+'~'+input('file path from')
    elif from_user == '7':
        return 'DDIR'+'~'+input('file path from')
    elif from_user == '8':
        return 'DDEL'+'~'+input('file path from')
    elif from_user == '9':
        return 'COPY'+'~'+input('file path from')+'~'+input('file path')
    elif from_user == '10':
        return 'GEXE'+'~'+input('file path from')
    elif from_user == '11':
        return input("enter free text data to send> ")
    else:
        return ''


def protocol_parse_reply(reply,sock):
    """
    parse the server reply and prepare it to user
    return: answer from server string
    """

    to_show = 'Invalid reply from server'
    try:
        reply = reply.decode()
        if '~' in reply:
            fields = reply.split('~')
        code = reply[:4]
        if code == 'TIMR':
            to_show = 'The Server time is: ' + fields[1]
        elif code == 'RNDR':
            to_show = 'Server draw the number: ' +  fields[1]
        elif code == 'WHOR':
            to_show = 'Server name is: ' +  fields[1]
        elif code == 'ERRR':
            to_show = 'Server return an error: ' + fields[1] + ' ' + fields[2]
        elif code == 'EXTR':
            to_show = 'Server acknowledged the exit message'
        elif code == 'SEXE':
            to_show = 'Server did the execute'
        elif code == 'SDIR':
            to_show = 'Server did the dir'+fields[1]
        elif code == 'SDEL':
            to_show = 'Server did the delete'
        elif code == 'COPS':
            to_show = 'Server did the copy'
        elif code == 'SNDF':
            to_show = 'Server started to send the file '
            put_in_file(sock)
        elif code == 'DSCR':
            to_show = 'Server did the scrren photo'
    except:
        print ('Server replay bad format')
    return to_show


def handle_reply(reply,sock):
    """
    get the tcp upcoming message and show reply information
    return: void
    """
    to_show = protocol_parse_reply(reply,sock)
    if to_show != '':
        print('\n==========================================================')
        print (f'  SERVER Reply: {to_show}   |')
        print(  '==========================================================')


def main(ip):
    """
    main client - handle socket and main loop
    """
    connected = False

    sock= socket.socket()

    port = 1234
    try:
        sock.connect((ip,port))
        print (f'Connect succeeded {ip}:{port}')
        connected = True
    except:
        print(f'Error while trying to connect.  Check ip or port -- {ip}:{port}')

    while connected:
        from_user = menu()
        to_send = protocol_build_request(from_user)
        if to_send =='':
            print("Selection error try again")
            continue
        try :
            send_with_size(sock,to_send)
            byte_data = recv_by_size(sock)   # todo improve it to recv by message size
            if byte_data == b'':
                print ('Seems server disconnected abnormal')
                break
            logtcp('recv',byte_data)
            handle_reply(byte_data,sock)

            if from_user == '4':
                print('Will exit ...')
                connected = False
                break
        except socket.error as err:
            print(f'Got socket error: {err}')
            break
        except Exception as err:
            print(f'General error: {err}')
            print(traceback.format_exc())
            break
    print ('Bye')
    sock.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('127.0.0.1')