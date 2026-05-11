import socket
import time

staip = "192.168.2.93"  # IP address shown after starting Docker
PORT = 8888

vflip_OFF  = "@vflip:0@"   # No vertical flip
vflip_OPEN = "@vflip:1@"   # Vertical flip enabled
mirror_OFF  = "@mirror:0@" # No horizontal mirror
mirror_OPEN = "@mirror:1@" # Horizontal mirror enabled


def set_Camera(vflip_flag, mirror_flag):
    if vflip_flag == True:
        send_data = vflip_OPEN
        sk.sendall(bytes(send_data, encoding="utf8"))
    elif vflip_flag == False:
        send_data = vflip_OFF
        sk.sendall(bytes(send_data, encoding="utf8"))

    time.sleep(1)

    if mirror_flag == True:
        send_data = mirror_OPEN
        sk.sendall(bytes(send_data, encoding="utf8"))
    elif mirror_flag == False:
        send_data = mirror_OFF
        sk.sendall(bytes(send_data, encoding="utf8"))


print("Please enter the Docker IPv4 address:")
staip = input()

sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server via TCP socket
try:
    sk.connect((staip, PORT))
    set_Camera(True, True)   # Flip the camera image
    # set_Camera(False, False) # Do not flip the camera image
    print("Camera settings applied successfully!")
    sk.close()
except KeyboardInterrupt:
    sk.close()
except Exception as e:
    print("Failed to apply camera settings!")
    print("Program Error:", e)  # Fixed: was printing the Exception class, not the instance
    sk.close()