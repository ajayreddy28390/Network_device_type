import paramiko
import time,json
#from netmiko import ConnectHandler
#from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
#import socket
import sys, re
import xmltodict,ipaddress
global remote_conn_pre,remote_conn


#multicast_ip = ipaddress.ip_address()

def disable_paging(remote_conn):
    '''Disable paging on a Cisco router'''

    remote_conn.send("terminal length 0\n")
    time.sleep(1)

    # Clear the buffer on the screen
    output = remote_conn.recv(1000)

def devicename_juniper(vendor):
    vendor_str = vendor.decode('utf-8')
    #print (vendor_str)
    output1 = re.search("<rpc-reply(.*?)</rpc-reply>", vendor_str, re.DOTALL).group()
    if output1:
        print("XML data output is being extracted")
        f = open('version.xml', "w+")
        f.write(output1)
        # seek to starting point
        f.seek(0)
        # open xml file to parse
        with open('version.xml') as fd:
            mydict = xmltodict.parse(fd.read())
        # print dict value
        return  mydict['rpc-reply']['software-information']['host-name']
    else:
        print ("No data. Check command")

def mc_info(dev_ip,mc_cmd,username,password):
    device_model(dev_ip,username=username,password=password)
    mc_info_op =run_command(mc_cmd)
    mc_xml_op=re.search("<rpc-reply(.*?)</rpc-reply>", mc_info_op, re.DOTALL).group()
    if mc_xml_op:
        print("XML data output is being extracted")
        f = open('version.xml', "w+")
        f.write(mc_xml_op)
        # seek to starting point
        f.seek(0)
        # open xml file to parse
        with open('version.xml') as fd:
            mydict = xmltodict.parse(fd.read())
        # print dict value
        return  mydict['rpc-reply']['software-information']['host-name']
    else:
        print ("No data. Check command")


def device_model(ip, username, password):
    # Create instance of SSHClient object
    global remote_conn_pre,remote_conn
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(
        paramiko.AutoAddPolicy())

    # initiate SSH connection
    remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
    print("SSH connection established to {0}".format(ip))

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    print("Interactive SSH session established")

    # Strip the initial router prompt
    output = remote_conn.recv(1000)

    # Turn off paging
    disable_paging(remote_conn)

    # Now let's try to send the router a command
    remote_conn.send("\n")
    '''
    remote_conn.send("show version | display xml | no-more\n")

    # Wait for the command to complete
    time.sleep(2)

    output = remote_conn.recv(50000)
    #device_model = re.search(r'(ios)|(Junos)|(Arista)', str(output), re.M | re.I)
    return output
    '''

def run_command(cmd):
    remote_conn.send(cmd)
    # Wait for the command to complete
    time.sleep(2)
    output = remote_conn.recv(50000)
    return output

def device2mgmtip(device):
    #print ("Provided device mgmt ip")
    # Read JSON file
    with open('device_mgmt_ip.json',encoding= 'UTF-8') as data_file:
        data_loaded = json.load(data_file)

    # print(json.dumps(data_loaded,sort_keys=True))
    for match in data_loaded['data']:
        for key, value in match.items():
            if (key == 'DEVICE' and value == device):
                device_mgmt_ip = match['IP']
                return device_mgmt_ip

def ip2devicemgmtip(ip):
    print ("Search device with ARP and get mgmt ip of device to login nexthop")
    try:
        for x in range(16):
            #print (x)
            with open('arp{}.json'.format(x+1),'r',encoding= 'UTF-8',errors='ignore') as data_file:
                #print ("Searching arp{}".format(x))
                data_loaded = json.load(data_file)
                for match in data_loaded['data']:
                    for key, value in match.items():
                        if (key == 'LOCALIP' and value == ip):
                            device_name = match['NAMESTRING']
                            return device_name
    except:
        print ("NOT ABLE TO PARSE JSON DATA")

    # print(json.dumps(data_loaded,sort_keys=True))

def main():
    global output, device_type
    ip_address = "159.125.43.156"
    mc_ip ="224.0.52.4"
    route_instance =""
    devicename = ip2devicemgmtip(ip_address)
    if devicename != None:
        print ("Device with IP in search:"+devicename)
        if devicename != None:
            print("Mgmt IP:"+device2mgmtip(devicename))

        device_model(ip=device2mgmtip(devicename) , username='amudimel', password='Wsxedc12')
        vendor = run_command("show version \n")
        device_type = re.search(r'(ios)|(Junos)|(Arista)', str(vendor), re.M | re.I)
        # print(device_type.group())
        if device_type.group().lower() == 'ios':
            print("Connected device vendor : Cisco " + device_type.group())
            device_type = 'cisco_ios'
        elif device_type.group().lower() == 'junos':
            print("Connected device vendor : Juniper " + device_type.group())
            device_type = 'juniper'
            vendor_jun = run_command(" show version | display xml | no-more\n")
            device_name = devicename_juniper(vendor_jun)
            print("Device Name:" + device_name)
            if devicename == device_name:
                print ("Device name matches with Records")
        elif device_type == 'Arista':
            print("Connected device vendor : " + device_type.group())
            device_type = 'Arista'
        else:
            print("Not recognized vendor")
    else:
        print ("NO DEVICE FOUND")



if __name__ == "__main__":
    main()