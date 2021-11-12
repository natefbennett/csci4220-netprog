import subprocess
import sys
import os
import subprocess
import time

class PeerData:

    def __init__(self, peer_id):
        self.id = peer_id
        self.invocation = ''
        self.inputs = []
        self.output = [] 

    # debug
    def __repr__(self):
        output = f'{self.id}: {self.invocation}\n'

        output += f'- inputs:\n'
        for line in self.inputs:
            output += f'\t{line}\n'

        output += f'- outputs:\n'
        for line in self.output:
            output += f'\t{line}\n'

        return output

class Test:

    def __init__(self, test_id):
        self.id = test_id
        self.peers = dict()
        self.cmd_calling_order = [] # keep a sequential list of peer_ids
                                    # to know what order to run commands
    def OnLastOutput(self):
        for peer in self.peers.values():
            if peer.output == []:
                return False

        return True

    # debug
    def __repr__(self):
        output = f'< TEST{self.id}: {len(self.peers)} peers\n'
        for peer in self.peers.values():
            output += f'{peer}\n'
        output += '>'
        return output

def TestParse(filename):

    test_dict = dict()
    with open(filename) as file:

        input_type = ''
        peer_id = ''
        cur_test = None
        cur_peer = None
        last_output = False

        for line in file:
            line = line.strip()

            # check for new test
            if '=' in line:
                test_id = int(line.strip('=').lstrip('TEST'))
                cur_test = Test(test_id)

            # read "header"
            elif 'Invocation' in line:
                input_type = 'invocation'
                continue

            elif 'Inputs' in line:
                input_type = 'input'
                continue

            elif 'output' in line:
                input_type = 'output'
                peer_id = line.split()[0]
                continue

            # data line
            else:
                # skip empty lines
                if not last_output:
                    if line.split() == []: continue

                if input_type == 'invocation':
                    id_num = line.split()[3]
                    if len(id_num) == 1:
                        id_num = f'0{id_num}'
                    peer_id = f'peer{id_num}'

                    peer = PeerData(peer_id)
                    peer.invocation = line

                    # add new peer to test
                    cur_test.peers[peer_id] = peer
                
                elif input_type == 'input':
                    line = line.lstrip('-->')
                    peer_id = line[:6]
                    cmd = line[8:]

                    # change bootstrap hostnames to localhost for local testing
                    cmd_split = cmd.split()
                    if cmd_split[0] == 'BOOTSTRAP':
                        cmd = f'BOOTSTRAP localhost {cmd_split[2]}'

                    cur_test.peers[peer_id].inputs.append(cmd)
                    cur_test.cmd_calling_order.append(peer_id)

                elif input_type == 'output':
                    last_output = cur_test.OnLastOutput()
                    cur_test.peers[peer_id].output.append(line)
                    if line.split() == [] and last_output:
                        test_dict[cur_test.id] = cur_test
                        last_output = False

    return test_dict

if __name__ == '__main__':

    # read in test filename
    # try:
    #     filename = sys.argv[1]
    # except:
    #     filename = sys.stdin.readline()
    filename = 'hw3_all_scripts.txt'

    print(f'Reading in tests from file: {filename} ...')
    test_dict = TestParse(filename)

    print(f'\nSelect a Test [1-{len(test_dict)}]:')
    for test_id in test_dict:
        print(f'{test_id}: =TEST{test_id}=')

    try:
        target_test_id = int(sys.argv[2])
    except:
        target_test_id = int(sys.stdin.readline())
    
    test = test_dict[target_test_id]

    print('Creating test files ...')

    folder_path = 'tmp_tests'
    if os.getcwd().split('/')[-1] == 'hw3':
        # checking whether folder exists or not
        if os.path.exists(folder_path):
            # checking whether the folder is empty or not
            if len(os.listdir(folder_path)) == 0:
                # removing the file using the os.remove() method
                os.rmdir(folder_path)
            else:
                # clear out folder of files
                for file in os.listdir(folder_path):
                    os.remove(f'{folder_path}/{file}')
        # folder does not exist
        else:
            os.mkdir(folder_path)
    else: print('Error: Must be in /hw3 directory to build tests!')
   
    procs = dict() # put all running instances of kad server here
    # write files for "peerXX-input.txt" and "peerXX-output.txt"
    for peer in test.peers.values():
        # create output files
        with open(f'{folder_path}/{peer.id}-output.txt', 'w') as peer_output:
            for line in peer.output:
                peer_output.write(f'{line}\n')

        # create input files
        with open(f'{folder_path}/{peer.id}-input.txt', 'w') as peer_input:
            for line in peer.inputs:
                peer_input.write(f'{line}\n')

        # start process, apture process output
        print(f'Starting SimpleKad: {peer.invocation}') #DEBUG
        # procs[peer.id] = subprocess.Popen(peer.invocation.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        procs[peer.id] = subprocess.Popen(peer.invocation.split(), stdin=subprocess.PIPE)
    print(f'Running Test {target_test_id} ...')
    # call commands in order, put output in file "test-peerXX-output.txt"
    for peer_id in test.cmd_calling_order:
        print(f'  command {peer_id}: {test.peers[peer_id].inputs[0]}') #DEBUG
        procs[peer_id].stdin.write(f'{test.peers[peer_id].inputs.pop(0)}\n'.encode('utf-8'))
        procs[peer_id].stdin.flush()
        time.sleep(1)
        # stdoutdata = procs[peer_id].stdout.readlines()
        # print(f'Got Response:\n{stdoutdata}') #DEBUG
        # with open(f'{folder_path}/test-{peer.id}-output.txt', 'a') as peer_output:
        #     peer_output.write(stdoutdata)

    
    

    # run bash script
    # compare output with diff