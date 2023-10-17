import serial.tools.list_ports as list_ports
import configparser
import logging



def discover(config_file = 'sheetjet.ini', save_config = True, load_config = True):
    """
    Find the addresses of all the serial device by either 
    loading them from a configuration file or by 
    manually unplugging and plugging in the device.
    
    Returns:
    Dictionary with the device name of each of the 3 
    devices: VCMini, TG5012A and MXII
    """
    ret = None
    if(load_config):
        ret = read_config(config_file)
        if ret is not None and None not in ret.values():
            return ret
        
    print('Performing manual USB address search.')
    if ret is None:
        ret = {}
    for d in ['VCMini', 'TG5012A', 'MXII']:
        if d not in ret or ret[d] is None:
            ret[d] = discover_device(d)
    if save_config:
        write_config(ret, config_file)
    return ret

def discover_device(name):
    print('Searching for %s' % (name))
    input('    Unplug the USB/Serial cable connected to %s. Press Enter when unplugged...' %(name))
    before = list_ports.comports()
    logging.debug('Devices found after unplugging:\n%s' %(format_devices_found(before)))
    input('    Reconnect the cable. Press Enter when the cable has been plugged in...')
    after = list_ports.comports()
    logging.debug('Devices found after replugging:\n%s' %(format_devices_found(after)))
    port = [i for i in after if i not in before]
    if(len(port) == 1):
        return DeviceInfo(port[0].device, port[0].hwid)
    elif(len(port) == 0):
        raise ConnectionError('No device found.')
    
    if(len(port) != 1):
        raise ConnectionError('Multiple devices changed!')
    return None

def format_devices_found(comports):
    ret = ''
    for p in comports:
        ret += "device:%s hwid:%s\n" % (p.device, p.hwid)
    return ret

def write_config(devices, config_file):
    config = configparser.ConfigParser()
    for d in devices:
        config[d] = devices[d].__dict__
    with open(config_file, 'w') as configfile:
        config.write(configfile)


def read_config(config_file, check_against_ports = True):
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
    except:
        logging.warning('Could not read config file %s' %(config_file))
        return None
    if(config.sections() == []):
        # Got empty config
        return None
    ret = {}
    for d in config.sections():
        ret[d] = DeviceInfo.from_config(config[d]) 

    if(check_against_ports is False):
        return ret
    
    ports = list_ports.comports()
    for d in ['VCMini', 'TG5012A', 'MXII']:
        found = False
        for p in ports:
            if(p.hwid == ret[d].hwid):
                logging.debug('Found %s with hwid %s at %s' %(d, p.hwid, p.device))
                found = True
                continue
        if found == False:
            logging.warning('Could not find %s with hwid %s' %(d, ret[d].hwid))
            ret[d] = None
    return ret


class DeviceInfo:
    def __init__(self, device, hwid):
        self.device = device
        self.hwid = hwid
    
    @classmethod
    def from_config(cls, config):
        if all(k in config for k in ('device', 'hwid')):
            return cls(config['device'], config['hwid'])
        else:
            return None
    
    def __str__(self):
        return 'device=%s hwid=%s' % (self.device, self.hwid)

    def __repr__(self):
        return 'DeviceInfo(device=%s, hwid=%s)' % (self.device, self.hwid)