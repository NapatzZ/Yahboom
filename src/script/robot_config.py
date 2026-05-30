import serial
import struct
import time
import socket
import subprocess

"""
ORDER is used to store the command address and corresponding data
"""
ORDER = {
    
    "WIFI_SSID": [0x01],
    "WIFI_PASSWD": [0x02],
    "AGENT_IP": [0x03, 0, 0, 0, 0],
    "AGENT_PORT": [0x04, 0, 0],
    "CAR_TYPE": [0x05, 0, 0],
    "DOMAIN_ID": [0x06, 0, 0],
    "SERIAL_BAUDRATE": [0x07, 0, 0, 0, 0],
    "SERVO_OFFSET": [0x08, 0, 0],
    "MOTOR_PID": [0x09, 0, 0, 0, 0, 0, 0],
    "IMU_YAW_PID": [0x0A, 0, 0, 0, 0, 0, 0],
    "ROS_NAMESPACE": [0x0B],

    "REBOOT_DEVICE": [0x20, 0x00, 0X00],
    "RESET_CONFIG": [0x21, 0x00, 0X00],

    "REQUEST_DATA": [0x50, 0, 0],
    "FIRMWARE_VERSION": [0x51],
}

class MicroROS_Robot():

    def __init__(self, port="/dev/ttyUSB0", debug=False):
        self.__ser = serial.Serial(port, 115200, timeout=0.05)
        self.__rx_FLAG = 0
        self.__rx_COUNT = 0
        self.__rx_ADDR = 0
        self.__rx_LEN = 0
        self.__RX_BUF_LEN_MAX = 40
        self.__rx_DATA = bytearray(self.__RX_BUF_LEN_MAX)
        self.__send_delay = 0.01
        self.__read_delay = 0.01
        self.__debug = debug

        self.__HEAD = 0xFF
        self.__DEVICE_ID = 0xF8
        self.__RETURN_ID = 0xF7
        self.__READ_DATA = 0x50

        self.AGENT_TYPE_WIFI_UDP = 0
        self.AGENT_TYPE_SERIAL = 1

        self.CAR_TYPE_COMPUTER = 0
        self.CAR_TYPE_RPI5 = 1
        self.CAR_TYPE_RISCV = 2

    # Send some data to device
    def __send(self, key, len=1):
        order = ORDER[key][0]
        value = []
        value_sum = 0
        for i in range(0, len):
            value.append(ORDER[key][1 + i])
            value_sum = value_sum + ORDER[key][1 + i]
        sum_data = (self.__HEAD + self.__DEVICE_ID + (len + 0x05) + order + value_sum) % 256
        tx = [self.__HEAD, self.__DEVICE_ID, (len + 0x05), order]
        tx.extend(value)
        tx.append(sum_data)
        self.__ser.write(tx)
        if self.__send_delay > 0:
            time.sleep(self.__send_delay)
        if self.__debug:
            print ("Send: [0x" + ', 0x'.join('{:02X}'.format(x) for x in tx) + "]")

    # Send request data
    def __request(self, addr, param=0):
        order = self.__READ_DATA
        buf_len = 7
        sum_data = (self.__HEAD + self.__DEVICE_ID + buf_len + order + addr + param) % 256
        tx = [self.__HEAD, self.__DEVICE_ID, buf_len, order, addr, param, sum_data]
        self.__ser.flushInput()
        self.__ser.flushOutput()
        for i in range(self.__RX_BUF_LEN_MAX):
            self.__rx_DATA[i] = 0
        self.__ser.write(tx)
        if self.__debug:
            print ("Read: [0x" + ', 0x'.join('{:02X}'.format(x) for x in tx) + "]")

    # Parse data
    def __unpack(self):
        n = self.__ser.inWaiting()
        rx_CHECK = 0
        if n:
            data_array = self.__ser.read_all()
            if self.__debug:
                print ("rx_data: [0x" + ', 0x'.join('{:02X}'.format(x) for x in data_array) + "]")
            for data in data_array:
                if self.__rx_FLAG == 0:
                    if data == self.__HEAD:
                        self.__rx_FLAG = 1
                    else:
                        self.__rx_FLAG = 0

                elif self.__rx_FLAG == 1:
                    if data == self.__RETURN_ID:
                        self.__rx_FLAG = 2
                    else:
                        self.__rx_FLAG = 0

                elif self.__rx_FLAG == 2:
                    self.__rx_LEN = data
                    self.__rx_FLAG = 3

                elif self.__rx_FLAG == 3:
                    self.__rx_ADDR = data
                    self.__rx_FLAG = 4
                    self.__rx_COUNT = 0

                elif self.__rx_FLAG == 4:
                    if self.__rx_COUNT < self.__rx_LEN - 5:
                        self.__rx_DATA[self.__rx_COUNT] = data
                        self.__rx_COUNT = self.__rx_COUNT + 1
                    if self.__rx_COUNT >= (self.__rx_LEN - 5):
                        self.__rx_FLAG = 5

                elif self.__rx_FLAG == 5:
                    for i in self.__rx_DATA:
                        rx_CHECK = rx_CHECK + i
                    rx_CHECK = (self.__HEAD + self.__RETURN_ID + self.__rx_LEN + self.__rx_ADDR + rx_CHECK) % 256
                    if data == rx_CHECK:
                        self.__rx_FLAG = 0
                        self.__rx_COUNT = 0
                        return True
                    else:
                        self.__rx_FLAG = 0
                        self.__rx_COUNT = 0
                        self.__rx_ADDR = 0
                        self.__rx_LEN = 0
        return False


    # Reboot device
    def reboot_device(self):
        self.__ser.setDTR(False)
        self.__ser.setRTS(True)
        time.sleep(.1)
        self.__ser.setDTR(True)
        self.__ser.setRTS(True)
        time.sleep(2)
    
    # Restore factory settings. Restart to take effect.
    def reset_factory_config(self):
        ORDER["RESET_CONFIG"][1] = 0x5F
        ORDER["RESET_CONFIG"][2] = 0x5F
        self.__send("RESET_CONFIG", len=2)
    
    # Configure the WiFi information, enter the WiFi signal name and password. Restart to take effect.
    def set_wifi_config(self, ssid, passwd):
        """
        Configure WiFi info, enter the WiFi signal name and password. Restart to take effect.
        Example input: ssid="ssid123", passwd="passwd123"
        """
        ssid_bytes = bytes(str(ssid), "utf-8")
        for i in range(len(ssid)):
            ORDER["WIFI_SSID"].append(ssid_bytes[i])
        self.__send("WIFI_SSID", len=len(ssid))
        passwd_bytes = bytes(str(passwd), "utf-8")
        for i in range(len(passwd)):
            ORDER["WIFI_PASSWD"].append(passwd_bytes[i])
        self.__send("WIFI_PASSWD", len=len(passwd))

    # Configure the WiFi proxy IP address and port number. Restart to take effect.
    def set_udp_config(self, ip, port):
        '''
        Configure the WiFi proxy IP address and port number. Restart to take effect.
        Example input: ip=[192,168,2,116], port=8090
        '''
        ORDER["AGENT_IP"][1] = int(ip[0]) & 0xFF
        ORDER["AGENT_IP"][2] = int(ip[1]) & 0xFF
        ORDER["AGENT_IP"][3] = int(ip[2]) & 0xFF
        ORDER["AGENT_IP"][4] = int(ip[3]) & 0xFF
        self.__send("AGENT_IP", len=4)
        ORDER["AGENT_PORT"][1] = int(port)&0xFF
        ORDER["AGENT_PORT"][2] = int(port>>8)&0xFF
        self.__send("AGENT_PORT", len=2)

    # Configure the baud rate for ROS serial communication. Restart to take effect.
    def set_ros_serial_baudrate(self, baudrate):
        '''
        Configure the ROS serial communication baud rate. Restart to take effect.
        Example input: baudrate=115200
        '''
        value_s = bytearray(struct.pack('i', int(baudrate)))
        ORDER["SERIAL_BAUDRATE"][1] = value_s[0]
        ORDER["SERIAL_BAUDRATE"][2] = value_s[1]
        ORDER["SERIAL_BAUDRATE"][3] = value_s[2]
        ORDER["SERIAL_BAUDRATE"][4] = value_s[3]
        self.__send("SERIAL_BAUDRATE", len=4)
    
    # Configure the ROS namespace. Restart to take effect.
    def set_ros_namespace(self, ros_namespace):
        """
        Configure the ROS namespace. Restart to take effect.
        Example input: ros_namespace="robot1"
        """
        name_len = len(ros_namespace)
        if name_len > 0:
            name_bytes = bytes(str(ros_namespace), "utf-8")
            for i in range(len(ros_namespace)):
                ORDER["ROS_NAMESPACE"].append(name_bytes[i])
        else:
            name_len = 1
            ORDER["ROS_NAMESPACE"].append(0)
        self.__send("ROS_NAMESPACE", len=name_len)

    # Configure the car type (agent mode). Restart to take effect.
    def set_car_type(self, car_type):
        '''
        Configure the car type (agent mode). Restart to take effect.
        Example input: car_type=0 = VM/computer version (WiFi proxy mode),
                       car_type=1 = Raspberry Pi version (serial proxy mode).
        '''
        ORDER["CAR_TYPE"][1] = int(car_type) & 0xFF
        ORDER["CAR_TYPE"][2] = 0
        self.__send("CAR_TYPE", len=2)

    # Configure the ROS DOMAIN ID. Restart to take effect.
    def set_ros_domain_id(self, domain_id):
        '''
        Configure ROS DOMAIN ID. Restart to take effect.
        Example input: domain_id=30. Valid range: 0 <= domain_id <= 100
        '''
        if domain_id > 100:
            domain_id = 100
        if domain_id < 0:
            domain_id = 0
        value_s = bytearray(struct.pack('h', int(domain_id)))
        ORDER["DOMAIN_ID"][1] = value_s[0]
        ORDER["DOMAIN_ID"][2] = value_s[1]
        self.__send("DOMAIN_ID", len=2)

    # Configure PWM servo offset angle.
    def set_pwm_servo_offset(self, servo_id, offset):
        '''
        Configure PWM servo offset angle.
        servo_id is the servo number: servo_id=1 operates servo S1, servo_id=2 operates servo S2.
        offset is the adjustment angle deviation. Valid range: [-6, 6]
        '''
        ORDER["SERVO_OFFSET"][1] = int(servo_id) & 0xFF
        ORDER["SERVO_OFFSET"][2] = int(offset) & 0xFF
        self.__send("SERVO_OFFSET", len=2)

    # Set motor PID parameters.
    def set_motor_pid_parm(self, pid_p, pid_i, pid_d):
        '''
        Set motor PID parameters.
        PID parameter valid range: [0.00, 10.00]
        '''
        pid_p_s = bytearray(struct.pack('h', int(pid_p*100)))
        pid_i_s = bytearray(struct.pack('h', int(pid_i*100)))
        pid_d_s = bytearray(struct.pack('h', int(pid_d*100)))
        ORDER["MOTOR_PID"][1] = pid_p_s[0]
        ORDER["MOTOR_PID"][2] = pid_p_s[1]
        ORDER["MOTOR_PID"][3] = pid_i_s[0]
        ORDER["MOTOR_PID"][4] = pid_i_s[1]
        ORDER["MOTOR_PID"][5] = pid_d_s[0]
        ORDER["MOTOR_PID"][6] = pid_d_s[1]
        self.__send("MOTOR_PID", len=6)

    # Set IMU YAW PID parameters.
    def set_imu_yaw_pid_parm(self, pid_p, pid_i, pid_d):
        '''
        Set IMU YAW PID parameters.
        PID parameter valid range: [0.00, 10.00]
        '''
        pid_p_s = bytearray(struct.pack('h', int(pid_p*100)))
        pid_i_s = bytearray(struct.pack('h', int(pid_i*100)))
        pid_d_s = bytearray(struct.pack('h', int(pid_d*100)))
        ORDER["IMU_YAW_PID"][1] = pid_p_s[0]
        ORDER["IMU_YAW_PID"][2] = pid_p_s[1]
        ORDER["IMU_YAW_PID"][3] = pid_i_s[0]
        ORDER["IMU_YAW_PID"][4] = pid_i_s[1]
        ORDER["IMU_YAW_PID"][5] = pid_d_s[0]
        ORDER["IMU_YAW_PID"][6] = pid_d_s[1]
        self.__send("IMU_YAW_PID", len=6)
    

    def read_wifi_ssid(self):
        '''
        Read the WiFi signal name the base board is connected to.
        '''
        self.__request(ORDER["WIFI_SSID"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            str_data = self.__rx_DATA.decode('utf-8')
        return str_data

    def read_wifi_passwd(self):
        '''
        Read the WiFi password stored on the base board.
        '''
        self.__request(ORDER["WIFI_PASSWD"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            str_data = self.__rx_DATA.decode('utf-8')
        return str_data

    def read_agent_ip_addr(self):
        '''
        Read the WiFi proxy IP address from the base board.
        '''
        self.__request(ORDER["AGENT_IP"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            str_data = "%d.%d.%d.%d" % (self.__rx_DATA[0], self.__rx_DATA[1], self.__rx_DATA[2], self.__rx_DATA[3])
        return str_data

    def read_agent_ip_port(self):
        '''
        Read the WiFi proxy IP port from the base board.
        '''
        self.__request(ORDER["AGENT_PORT"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            port = struct.unpack('h', bytearray(self.__rx_DATA[0:2]))[0]
            str_data = "%d" % (port)
        return str_data

    def read_car_type(self):
        '''
        Read the car type and agent connection mode from the base board.
        '''
        self.__request(ORDER["CAR_TYPE"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            agent = struct.unpack('h', bytearray(self.__rx_DATA[0:2]))[0]
            if agent == self.CAR_TYPE_COMPUTER:
                str_data = "CAR_TYPE_COMPUTER"
            elif agent == self.CAR_TYPE_RPI5:
                str_data = "CAR_TYPE_RPI5"
            elif agent == self.CAR_TYPE_RISCV:
                str_data = "CAR_TYPE_RISCV"
            else:
                str_data = "unknow"
        return str_data

    def read_ros_domain_id(self):
        '''
        Read the ROS DOMAIN ID from the base board.
        '''
        self.__request(ORDER["DOMAIN_ID"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            domain_id = struct.unpack('h', bytearray(self.__rx_DATA[0:2]))[0]
            str_data = "%d" % (domain_id)
        return str_data

    def read_ros_serial_baudrate(self):
        '''
        Read the ROS serial communication baud rate from the base board.
        '''
        self.__request(ORDER["SERIAL_BAUDRATE"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            baudrate = struct.unpack('i', bytearray(self.__rx_DATA[0:4]))[0]
            str_data = "%d" % (baudrate)
        return str_data
    
    def read_ros_namespace(self):
        '''
        Read the ROS namespace from the base board.
        '''
        self.__request(ORDER["ROS_NAMESPACE"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            str_data = self.__rx_DATA.decode('utf-8')
        return str_data

    def read_pwm_servo_offset(self):
        '''
        Read the PWM servo offset angle from the base board.
        '''
        self.__request(ORDER["SERVO_OFFSET"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            offset_s1 = struct.unpack('b', bytearray(self.__rx_DATA[0:1]))[0]
            offset_s2 = struct.unpack('b', bytearray(self.__rx_DATA[1:2]))[0]
            str_data = "%d, %d" % (offset_s1, offset_s2)
        return str_data

    def read_motor_pid_parm(self):
        '''
        Read the motor PID parameters from the base board.
        '''
        self.__request(ORDER["MOTOR_PID"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            pid_p = struct.unpack('h', bytearray(self.__rx_DATA[0:2]))[0]/100.0
            pid_i = struct.unpack('h', bytearray(self.__rx_DATA[2:4]))[0]/100.0
            pid_d = struct.unpack('h', bytearray(self.__rx_DATA[4:6]))[0]/100.0
            str_data = "%.2f, %.2f, %.2f" % (pid_p, pid_i, pid_d)
        return str_data

    def read_imu_yaw_pid_parm(self):
        '''
        Read the IMU YAW PID parameters from the base board.
        '''
        self.__request(ORDER["IMU_YAW_PID"][0])
        time.sleep(self.__read_delay)
        str_data = None
        if self.__unpack():
            pid_p = struct.unpack('h', bytearray(self.__rx_DATA[0:2]))[0]/100.0
            pid_i = struct.unpack('h', bytearray(self.__rx_DATA[2:4]))[0]/100.0
            pid_d = struct.unpack('h', bytearray(self.__rx_DATA[4:6]))[0]/100.0
            str_data = "%.2f, %.2f, %.2f" % (pid_p, pid_i, pid_d)
        return str_data

    def read_version(self):
        '''
        Return the firmware version.
        '''
        self.__request(ORDER["FIRMWARE_VERSION"][0])
        time.sleep(self.__read_delay)
        str_version = None
        if self.__unpack():
            str_version = "%d.%d.%d" % (self.__rx_DATA[0], self.__rx_DATA[1], self.__rx_DATA[2])
        return str_version

    # Read and print all configuration information.
    def print_all_firmware_parm(self):
        version = self.read_version()
        print("version:", version)

        ssid = self.read_wifi_ssid()
        print("ssid:", ssid)
        passwd = self.read_wifi_passwd()
        print("passwd:", passwd)

        ip_addr = self.read_agent_ip_addr()
        print("ip_addr:", ip_addr)
        ip_port = self.read_agent_ip_port()
        print("ip_port:", ip_port)

        car_type = self.read_car_type()
        print("car_type:", car_type)

        domain_id = self.read_ros_domain_id()
        print("domain_id:", domain_id)

        baudrate = self.read_ros_serial_baudrate()
        print("ros_serial_baudrate:", baudrate)

        ros_namespace = self.read_ros_namespace()
        print("ros_namespace:", ros_namespace)

        servo_offset = self.read_pwm_servo_offset()
        print("servo_offset:", servo_offset)

        motor_pid_parm = self.read_motor_pid_parm()
        print("motor pid parm:", motor_pid_parm)

        imu_pid_parm = self.read_imu_yaw_pid_parm()
        print("imu yaw pid parm:", imu_pid_parm)

def get_active_wifi_info():
    """Extracts the active WiFi SSID and password, supporting both Linux (nmcli) and macOS."""
    # Linux: nmcli
    try:
        conn_cmd = "nmcli -t -f NAME,TYPE connection show --active | grep 802-11-wireless | cut -d: -f1"
        conn_name = subprocess.check_output(conn_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if conn_name:
            pwd_cmd = f"nmcli -s -g 802-11-wireless-security.psk connection show '{conn_name}'"
            pwd = subprocess.check_output(pwd_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            return conn_name, pwd
    except Exception:
        pass

    # macOS: airport + security keychain
    try:
        airport = ('/System/Library/PrivateFrameworks/Apple80211.framework'
                   '/Versions/Current/Resources/airport')
        raw = subprocess.check_output([airport, '-I'], stderr=subprocess.DEVNULL).decode('utf-8')
        ssid = None
        for line in raw.splitlines():
            if ' SSID:' in line:
                ssid = line.split('SSID:', 1)[1].strip()
                break
        if ssid:
            pwd = subprocess.check_output(
                ['security', 'find-generic-password', '-D', 'AirPort network password', '-a', ssid, '-w'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            return ssid, pwd
    except Exception:
        pass

    return None, None

def get_local_ip():
    """Dynamically finds the computer's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return [int(x) for x in ip.split('.')]
    except Exception:
        return [192, 168, 1, 100]

if __name__ == '__main__':
    robot = MicroROS_Robot(port='/dev/tty.usbserial-0001', debug=False)
    print("Rebooting Device, Please wait.")
    robot.reboot_device()

    # Auto-detect Network Information
    ssid, passwd = get_active_wifi_info()
    local_ip = get_local_ip()

    if ssid and passwd:
        print(f"Auto-detected WiFi: {ssid}")
        robot.set_wifi_config(ssid, passwd)
    else:
        print("Warning: Could not auto-detect WiFi. Using fallback values.")
        robot.set_wifi_config("Napat", "turtlebot")

    print(f"Auto-detected Agent IP: {local_ip}")
    robot.set_udp_config(local_ip, 8090)

    robot.set_car_type(robot.CAR_TYPE_COMPUTER)
    # robot.set_car_type(robot.CAR_TYPE_RPI5)
    # robot.set_car_type(robot.CAR_TYPE_RISCV)
    robot.set_ros_domain_id(20)
    robot.set_ros_serial_baudrate(921600)
    robot.set_ros_namespace("")
    robot.set_pwm_servo_offset(1, 0)
    robot.set_pwm_servo_offset(2, 0)
    robot.set_motor_pid_parm(1, 0.2, 0.2)
    robot.set_imu_yaw_pid_parm(1, 0, 0.2)

    time.sleep(.1)
    robot.print_all_firmware_parm()

    print("\nRebooting device to apply config...")
    robot.reboot_device()
    print("Done. Robot is rebooting — wait ~10s for it to join WiFi, then check the agent.")
    del robot
