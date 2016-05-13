import paramiko
import os
import select
import sys
import Xlib.support.connect as xlib_connect

def run(transport, session, command):
    def x11_handler(channel, (src_addr, src_port)):
        x11_fileno = channel.fileno()
        local_x11_channel = xlib_connect.get_socket(*local_x11_display[:3])
        local_x11_fileno = local_x11_channel.fileno()

        # Register both x11 and local_x11 channels
        channels[x11_fileno] = channel, local_x11_channel
        channels[local_x11_fileno] = local_x11_channel, channel

        poller.register(x11_fileno, select.POLLIN)
        poller.register(local_x11_fileno, select.POLLIN)

        transport._queue_incoming_channel(channel)

    def flush_out(channel):
        while channel.recv_ready():
            sys.stdout.write(channel.recv(4096))
        while channel.recv_stderr_ready():
            sys.stderr.write(channel.recv_stderr(4096))

    local_x11_display = xlib_connect.get_display(os.environ['DISPLAY'])

    channels = {}
    poller = select.poll()
    session_fileno = session.fileno()
    poller.register(session_fileno)

    session.request_x11(handler=x11_handler)
    session.exec_command('xclock')
    transport.accept()

    # event loop
    while not session.exit_status_ready():
        poll = poller.poll()
        if not poll: # this should not happen, as we don't have a timeout.
            break
        for fd, event in poll:
            if fd == session_fileno:
                flush_out(session)
            # data either on local/remote x11 channels/sockets
            if fd in channels.keys():
                sender, receiver = channels[fd]
                try:
                    receiver.sendall(sender.recv(4096))
                except:
                    sender.close()
                    receiver.close()
                    channels.remove(fd)

    flush_out(session)
    return session.recv_exit_status()

if __name__ == '__main__':
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect('10.0.0.11', username='opti', password='opti')
    transport = ssh_client.get_transport()
    session = transport.open_session()
    run(transport, session, 'xterm')