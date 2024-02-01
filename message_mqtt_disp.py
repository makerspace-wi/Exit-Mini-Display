#!/usr/bin/env python3
""" 
Checken die gesendeten Zeichnen: [over commands]
Display 240 x 320 [Height,Width]
msg.topic -- |  msg.payload ----------------
MQTT_TOPIC   | 'txt;abcdef'  # Text 
MQTT_TOPIC   | 'txp;0,0'     # Text position x,y [max. 320, 240]
MQTT_TOPIC   | 'txs;0,0'     # Text size x,y [max. 320, 240]
MQTT_TOPIC   | 'txc;0,0,0'   # Text color r,g,b [0 - 255]
MQTT_TOPIC   | 'clc;'        # Clear display [+ text position = 0]
MQTT_TOPIC   | 'del;'        # Delete text at last position
MQTT_TOPIC   | 'tfn;0'       # Text Font Nr.0
MQTT_TOPIC   | 'tfh;20'      # Text Font height [20]
MQTT_TOPIC   | 'bgb;1.0'     # Background brightness [0 - 1.0]
MQTT_TOPIC   | 'bgc;0,0,0'   # Background color r,g,b [0 - 255]
MQTT_TOPIC   | 'led;0,0,0'   # Led r,g,b light [0 - 1.0]

 msg.topic - |  msg.publish ----------------
MQTT_PUBLI   | 'DISP;POR;'   # publish after start
MQTT_PUBLI   | 'OK'          # publish after every command 
MQTT_PUBLI'  | 'SIZE;0,0'    # publish text size lenght, height
MQTT_PUBLI'  | 'BUTT;?'      # publish button ? = A,B,X,Y
"""
Version = "V1.0.1"

from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

import paho.mqtt.client as mqtt

# Mqtt
MQTT_SERVER = "192.168.1.252"
MQTT_PORT   = 1884
MQTT_TOPIC  = "display/exit/"
MQTT_PUBLI  = "display/exit/pub"
MQTT_POR    = "DISP;POR;"
MQTT_OK     = "OK"
MQTT_TXTPOS = "POS;"
MQTT_ERR    = "Error;"

# Variables -------------------------------------
vtpx = 0      # [0] Text position X (320)
vtpy = 0      # [0] Text position Y (240)
vtsx = 0      # [0] Text size X
vtsy = 0      # [0] Text size Y
vtcr = 255    # [255] Text Color R (0 - 255)
vtcg = 255    # [255] Text Color G (0 - 255)
vtcb = 255    # [255] Text Color B (0 - 255)
vtfn = 0      # [0] Value Text Font Nr.
vtfh = 25     # [25] Value Text Font height
vbgb = 1.0    # [1.0] Background brightness (0.0 - 1.0)
vbgcr = 0     # [0] Background color R (0 - 255)
vbgcg = 0     # [0] Background color G (0 - 255)
vbgcb = 0     # [0] Background color B (0 - 255)
vledr = 0.0 # [0] Led color brightness R (0.0 - 1.0)
vledg = 0.0 # [0] Led color brightness G (0.0 - 1.0)
vledb = 0.0 # [0] Led color brightness B (0.0 - 1.0)
# Font tuple
fonttu = ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

#Init -----------------------
width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT
buffer = Image.new("RGB", (width, height), color=(vbgcr, vbgcg, vbgcb))
draw = ImageDraw.Draw(buffer)
displayhatmini = DisplayHATMini(buffer, backlight_pwm=True)
displayhatmini.set_led(vledr, vledg, vledb)

# Display HAT Mini button presses publish
def button_callback(pin):
#    print("Button Pressed: " + str(pin))
    if pin == 5:
        client.publish(MQTT_PUBLI, "BUTT;A")
    elif pin == 6:
        client.publish(MQTT_PUBLI, "BUTT;B")
    elif pin == 16:
        client.publish(MQTT_PUBLI, "BUTT;X")
    elif pin == 24:
        client.publish(MQTT_PUBLI, "BUTT;Y")

displayhatmini.on_button_pressed(button_callback)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)
    draw.text((vtpx, vtpy), "Display " + Version, font=ImageFont.truetype(fonttu[vtfn], vtfh), fill=(vtcr, vtcg, vtcb))    #Text
    displayhatmini.display()
    displayhatmini.set_backlight(vbgb)
    client.publish(MQTT_PUBLI, MQTT_POR + Version)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global vledr, vledg, vledb, vbgcr,vbgcg,vbgcb,vbgb
    global vtsx,vtsy,vtpx,vtpy,vtfh,vtfn,vtcr,vtcg,vtcb
    top = str(msg.topic)
    msa = str(msg.payload)
    i = msa.find("'") + 1
    if msa.count("'") == 2:
        cmd = msa[i:-1]
        if cmd.find(";") == 3:
            val = cmd[4:]
            cmd = cmd[:3]
            if cmd == "led":    # led color
                if val.count(",") == 2:
                    p1 = val.find(",")
                    p2 = val.find(",",p1 + 1)
                    vledr = float(val[:p1])
                    vledg = float(val[p1 + 1:p2])
                    vledb = float(val[p2 + 1:])
                    displayhatmini.set_led(vledr, vledg, vledb)
                    client.publish(MQTT_PUBLI, "OK")
            elif cmd == "bgc":  # background color
                if val.count(",") == 2:
                    p1 = val.find(",") 
                    p2 = val.find(",",p1 + 1)
                    vbgcr = int(val[:p1])
                    vbgcg = int(val[p1 + 1:p2])
                    vbgcb = int(val[p2 + 1:])
                    draw.rectangle((0, 0, width, height), (vbgcr, vbgcg, vbgcb)) # Background
                    displayhatmini.display()
                    client.publish(MQTT_PUBLI, "OK")
            elif cmd == "bgb":  # background brightness
                vbgb = float(val)
                displayhatmini.set_backlight(vbgb)
                client.publish(MQTT_PUBLI, "OK")
            elif cmd == "tfh": # text font height
                vtfh = int(val)
                client.publish(MQTT_PUBLI, "OK")
            elif cmd == "tfn": # text font number
                vtfn = int(val)
                client.publish(MQTT_PUBLI, "OK")
            elif cmd == "clc": # clear display
                draw.rectangle((0, 0, width, height), (vbgcr, vbgcg, vbgcb)) # Background
                vtpx = 0; vtpy = 0
                displayhatmini.display()
                client.publish(MQTT_PUBLI, "OK")
            elif cmd == "del": # delete text
                draw.rectangle((vtpx + vtsx, vtpy + vtsy, vtpx, vtpy), (vbgcr, vbgcg, vbgcb)) # Background
                displayhatmini.display()
                client.publish(MQTT_PUBLI, "OK")
            elif cmd == "txc": # text color
                if val.count(",") == 2:
                    p1 = val.find(",")
                    p2 = val.find(",",p1 + 1)
                    vtcr = int(val[:p1])
                    vtcg = int(val[p1 + 1:p2])
                    vtcb = int(val[p2 + 1:])
                    client.publish(MQTT_PUBLI, "OK")
            elif cmd == "txs": # text size
                if val.count(",") == 1:
                    p1 = val.find(",")
                    vtsx = int(val[:p1])
                    vtsy = int(val[p1 + 1:])
                    client.publish(MQTT_PUBLI, "OK")
            elif cmd == "txp": # text position
                if val.count(",") == 1:
                    p1 = val.find(",")
                    vtpx = int(val[:p1])
                    vtpy = int(val[p1 + 1:])
                    client.publish(MQTT_PUBLI, "OK")
            elif cmd == "txt": # text
                vtsx, vtsy = draw.textsize(val, ImageFont.truetype(fonttu[vtfn], vtfh))
                draw.text((vtpx, vtpy), val, font=ImageFont.truetype(fonttu[vtfn], vtfh), fill=(vtcr, vtcg, vtcb))    #Text
                displayhatmini.display()
                client.publish(MQTT_PUBLI, "SIZE;" + str(vtsx) + "," + str(vtsy))
            else:
                client.publish(MQTT_PUBLI, MQTT_ERR + cmd + "?" + val)
        else:
            client.publish(MQTT_PUBLI, MQTT_ERR + cmd)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
 
client.connect(MQTT_SERVER, MQTT_PORT, 60)
 
client.loop_forever()
