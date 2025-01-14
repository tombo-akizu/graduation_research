import socket

import logger   # type: ignore

def get_method_bits():
    target_ip = "127.0.0.1"
    target_port = 8080
    buffer_size = 4096

    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tcp_client.connect((target_ip,target_port))

    method_bits = 0
    response = tcp_client.recv(buffer_size)
    for i, b in enumerate(response):
        method_bits |= (b << (8 * i))

    tcp_client.close()

    logger.logger.debug("Method Bits: {}".format(method_bits))
    return method_bits