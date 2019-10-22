import time
from _socket import socket
import threading
from functools import reduce
from typing import List

from Buffer import Buffer

from Buffer import RobotNotInUsername, InfoOrFoto, FotoException, BadCheckSum


class ClientHandler(threading.Thread):
    FIRST_MESSAGE = '201 PASSWORD\r\n'
    SECOND_MESSAGE = '202 OK\r\n'

    LOGIN_FAILED = '500 LOGIN FAILED\r\n'
    SYNTAX_ERROR = '501 SYNTAX ERROR\r\n'
    TIMEOUT = '502 TIMEOUT\r\n'

    BAD_CHECKSUM = '300 BAD CHECKSUM\r\n'

    def __init__(self, connection: socket):
        self.connection = connection
        self.buffer = Buffer()
        self.step = 0
        self.username = None
        self.stop_event = threading.Event()
        self.username_wrong = None
        self.start_time = time.time()
        super().__init__()

    def end_with_message(self, message):
        self.connection.sendall(message.encode())
        self.connection.close()
        self.stop_event.set()

    def run(self,):
        while not self.stop_event.is_set():
            if time.time() - self.start_time >= 1111145:
                self.end_with_message(self.TIMEOUT)
                print(f'stopped {self.ident} thread: TIMEOUT')
                return
            data = self.connection.recv(1)
            if self.buffer.state == 0:
                try:
                    username_sum = self.buffer.process_byte(data)
                    if username_sum:
                        self.username = username_sum
                        self.connection.sendall(self.FIRST_MESSAGE.encode())
                except RobotNotInUsername:
                    self.username_wrong = True
            elif self.buffer.state == 1:
                if self.username_wrong:
                    self.end_with_message(self.LOGIN_FAILED)
                password = self.buffer.process_byte(data)
                if password:
                    if int(password) == self.username:
                        self.connection.sendall(self.SECOND_MESSAGE.encode())
                    else:
                        self.end_with_message(self.LOGIN_FAILED)
            elif self.buffer.state == 2:
                try:
                    reading_succ = self.buffer.process_byte(data)
                    if reading_succ:
                        self.connection.sendall(self.SECOND_MESSAGE.encode())
                except BadCheckSum:
                    self.connection.sendall(self.BAD_CHECKSUM.encode())
                    return
                except FotoException:
                    self.end_with_message(self.SYNTAX_ERROR)
                    return
                except InfoOrFoto:
                    self.end_with_message(self.SYNTAX_ERROR)
                    return
        print('------------' * 5)
        print(vars(self.buffer))
        print('------------' * 5)
        print(f'stopped {self.ident} thread: END')
        return

    def join(self, **kwargs):
        if not self.stop_event.is_set():
            self.stop_event.set()
        super().join(**kwargs)
        

    # def create_response(self, words: list) -> [str, None]:
    #     if self.step == 0:
    #         self.step += 1
    #         self.handle_first_step(words)
    #         return self.FIRST_MESSAGE
    #     elif self.step == 1:
    #         self.step += 1
    #         if self.handle_second_step(words):
    #             return self.SECOND_MESSAGE
    #         else:
    #             self.bad_checksum.set()
    #             return None
    #     elif self.step == 2:
    #         return self.handle_third_step(words)
    #
    # def handle_first_step(self, words: List):
    #     self.username = words[0]
    #     return True
    #
    # def handle_second_step(self, words: List):
    #     password = reduce(lambda x, y: x+y, list(map(ord, [x for x in self.username])))
    #     try:
    #         entered_pass = int(words[0])
    #     except Exception:
    #         return False
    #     return password == entered_pass





