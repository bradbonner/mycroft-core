# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.
import subprocess
import sys
from Queue import Queue
from alsaaudio import Mixer
from threading import Thread

import os
import serial
import time

import threading

from mycroft.client.enclosure.arduino import EnclosureArduino
from mycroft.client.enclosure.eyes import EnclosureEyes
from mycroft.client.enclosure.mouth import EnclosureMouth
from mycroft.client.enclosure.weather import EnclosureWeather
from mycroft.configuration import ConfigurationManager
from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from mycroft.util import kill, str2bool
from mycroft.util import play_wav
from mycroft.util.log import getLogger
from mycroft.util.audio_test import record

__author__ = 'aatchison'

#mycroft stuff
from mycroft.configuration import ConfigurationManager
from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from mycroft.util import kill, str2bool
from mycroft.util.log import getLogger

#wifi setup stuff
import Queue
import os
import sys
import threading
import time
from operator import itemgetter
import tornado.ioloop
import tornado.template
import tornado.web
import tornado.websocket
from app.util.Config import AppConfig
from app.util.FileUtils import ap_mode_config, write_hostapd_conf, write_network_interfaces, write_dnsmasq
from app.util.LinkUtils import ScanForAP, link_add_vap
from app.util.WiFiTools import ap_link_tools,dev_link_tools, hostapd_tools
from app.util.dnsmasqTools import dnsmasqTools
from app.util.hostAPDTools import hostAPServerTools
from app.util.Server import MainHandler, JSHandler, BootstrapMinJSHandler, BootstrapMinCSSHandler, WSHandler
from app.util.wpaCLITools import wpaClientTools
#

LOGGER = getLogger("WiFiSetupClient")

#config = AppConfig()
#config.open_file()
#Port = config.ConfigSectionMap("server_port")['port']
#WSPort = config.ConfigSectionMap("server_port")['ws_port']
dev_link_tools = dev_link_tools()
linktools = ap_link_tools()

root = os.path.join(os.path.dirname(__file__), "srv/templates")

handlers = [
    (r"/", MainHandler),
    (r"/jquery-2.2.3.min.js",JSHandler),
    (r"/img/(.*)", tornado.web.StaticFileHandler, { 'path': os.path.join(root, 'img/') } ),
    (r"/bootstrap-3.3.7-dist/css/bootstrap.min.css",BootstrapMinCSSHandler),
    (r"/bootstrap-3.3.7-dist/js/bootstrap.min.js",BootstrapMinJSHandler),
    (r"/ws",WSHandler)
]
settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "./srv/templates"),
)

exitFlag = 0

class WiFiSetup:
    def __init__(self):
        self.client = WebsocketClient()
        self.__register_wifi_events()
    def setup(self):
        must_start_ap_mode = True
        if must_start_ap_mode is not None and must_start_ap_mode is True:
            LOGGER.info("Initalizing wireless setup mode.")
            self.client.emit(Message("speak", metadata={
                'utterance': "Initializing wireless setup mode."}))
    def run(self):
        try:
            self.client.run_forever()
        except Exception as e:
            LOGGER.error("Client error: {0}".format(e))
            self.stop()

    @staticmethod
    def stop(self):
        LOGGER.info("Shut down wireless setup mode.")

    def __register_events(self):
        self.client.on('recognizer_loop:record_begin', self.__update_events)
        self.__register_wifi_events()


    def __wifi_listeners(self, event=None):
        if event and event.metadata:
            active = event.metadata['active']
            if active:
                self.__register_wifi_events()
            else:
                self.__remove_wifi_events()


    def __register_wifi_events(self):
        self.client.on('recognizer_loop:record_begin',self.test_event())


    def __remove_wifi_events(self):
        self.client.remove('recognizer_loop:record_begin', self.test_event())

    def __update_events(self, event=None):
        if event and event.metadata:
            if event.metadata.get('paired', False):
                self.__register_wifi_events()
            else:
                self.__remove_wifi_events()

    def test_event(self):
        print "event triggered"




class tornadoWorker (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        print "Starting " + self.name + str(self.threadID)
        #process_data(self.name, self.q)
        ws_app = tornado.web.Application([(r'/ws', WSHandler), ])
        ws_app.listen('8888')#Port)
        app = tornado.web.Application(handlers, **settings)
        app.listen('80')
        tornado.ioloop.IOLoop.current().start()
        #print "Exiting " + self.name

class apWorker (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        print "Starting " + self.name + str(self.threadID)
        #apScan = ScanForAP('scan', 'uap0')
        #apScan.start()
        #apScan.join()
        #ap = apScan.join()

        #################################################
        # Clean up the list of networks.
        #################################################
        # First, sort by name and strength
        nets_byNameAndStr = sorted(ap['network'], key=itemgetter('ssid', 'quality'), reverse=True)
        # now strip out duplicates (e.g. repeaters with the same SSID), keeping the first (strongest)
        lastSSID = "."
        for n in nets_byNameAndStr[:]:
            if (n['ssid'] == lastSSID):
                nets_byNameAndStr.remove(n)
            else:
                lastSSID = n['ssid']
                # Finally, sort by strength alone
            ap['network'] = sorted(nets_byNameAndStr, key=itemgetter('quality'), reverse=True)
        # ap = linktools.scan_ap()
        S = Station()
        try:
            print "station on"
            S.station_mode_on()
        except:
            exit(0)
        #process_data(self.name, self.q)
        #print "Exiting " + self.name

class dnsmasqWorker (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        print "Starting " + self.name + str(self.threadID)

        try:
            print "dnsmasq on"
            S.dnsmasq_on()
        except:
            exit(0)

class Station():
    def __init__(self):
        self.aptools = hostapd_tools()
    def station_mode_on(self):
        print "station mode on"
        ap_mode_config()
        print init_stop_services()
        time.sleep(2)
        print init_set_interfaces()
        time.sleep(2)
        print init_hostap_mode()
        #self.aptools.hostapd_start()
        #self.aptools.dnsmasq_start()

        #aptools.ap_config()
# SSP: Temporary change while developing
#        AP.copy_config_ap()
#        devtools.link_down()
#        aptools.ap_up()

    def station_mode_off(self):
        print "station mode off"
        self.aptools.dnsmasq_stop()
        self.aptools.hostapd_stop()

    def dnsmasq_on(self):
        self.aptools.dnsmasq_start()

    def dnsmasq_off(self):
        self.aptools.dnsmasq_stop()
# SSP: Temporary change while developing
#        aptools.ap_down()
#        aptools.ap_deconfig()
#        devtools.link_down()
#        devtools.link_up()

def init_stop_services():
    WPATools.wpa_cli_flush()
    DNSTools.dnsmasqServiceStop()
    APTools.hostAPDStop()
    return "STOPPED services"

def init_set_interfaces():
    write_network_interfaces('wlan0','uap0', '172.24.1.1', 'bc:5f:f4:be:7d:0a')
    link_add_vap()
    return "SETUP interfaces"

def init_hostap_mode():
    write_hostapd_conf('uap0','nl80211','mycroft',11)
    write_dnsmasq('uap0','172.24.1.1','172.24.1.10','172.24.1.20')
    APTools.hostAPDStart()
    DNSTools.dnsmasqServiceStart()
    return APTools.hostAPDStatus()

def try_connect():
    network_id = WPATools.wpa_cli_add_network('wlan0')
    print network_id
    # print wpa_cli_flush()
    print WPATools.wpa_cli_set_network('wlan0', '0', 'ssid', '"Entrepreneur"')
    print WPATools.wpa_cli_set_network('wlan0', '0', 'psk', '"startsomething"')
    print WPATools.wpa_cli_enable_network('wlan0', '0')

def exit_gracefully(signal, frame):
    INIT = False
    print "caught SIGINT"
    S = Station()
    #ap_mode_deconfig()
    S.station_mode_off()
    S.dnsmasq_off()
    print "exiting"
    sys.exit(0)



nameList = ['web','ap', 'dns']
queueLock = threading.Lock()
workQueue = Queue.Queue(10)
threads = []
threadID = 1

def main():
    try:
        wifi_setup = WiFiSetup()
        t = threading.Thread(target=wifi_setup.run)
        t.start()
        wifi_setup.setup()
        t.join()
    except Exception as e:
        print (e)
    finally:
        sys.exit()

if __name__ == "__main__":
    main()



##    signal.signal(signal.SIGINT, exit_gracefully)


    # New
##    WPATools = wpaClientTools()
##    APTools = hostAPServerTools()
##    DNSTools = dnsmasqTools()

##    S = Station()
##    S.station_mode_on()

    # new vars

##    INIT = True
    #try_connect()
##    if INIT is True:
##        ap = ScanForAP("AP SCAN: ", 'uap0')

##        thread = apWorker(threadID, 'ap', workQueue)
##        thread.setDaemon(True)
##        thread.start()
##        threads.append(thread)
##        threadID += 1
##        thread.join()

##        thread = tornadoWorker(threadID, 'web', workQueue)
##        thread.setDaemon(True)
##        thread.start()
##        threads.append(thread)
##        threadID += 1
        #thread.join()


##    while INIT is True:
##        print "ok"
##        try:
##            if WiFi.wpa_cli_status('wlan0')['wpa_state'] == 'COMPLETED':
##                print "CONNECTED"
##                INIT = False
##        except:
##            print "no"
##            time.sleep(1)


        #or t in threads:
        #   t.is_alive()
        #   t.join()


    #client_connect_test('wlan0', 'MOTOROLA-F29E5', '2e636e8543dc97ee7299')

    #link_add_vap()
    #ap = ScanForAP("AP SCAN: ", 'uap0')
    #ap.start()
    #print ap.join()
    #client_connect_test('wlan0', 'MOTOROLA-F29E5', '2e636e8543dc97ee7299')
    # Create new threads
    #for tName in threadList:
    ##thread = tornadoWorker(threadID, 'web', workQueue)
    ##thread.setDaemon(True)
    ##thread.start()
    ##threads.append(thread)
    ##threadID += 1
    #thread = apWorker(threadID, 'ap', workQueue)
    #thread.setDaemon(True)
    #thread.start()
    #threads.append(thread)
    #threadID += 1
    #thread = dnsmasqWorker(threadID, 'dns', workQueue)
    #thread.start()
    #threads.append(thread)
    #threadID += 1
    ##print threading.enumerate()
    # Fill the queue
    ##queueLock.acquire()
    #for word in nameList:
    #    workQueue.put(word)
    ##queueLock.release()

    # Wait for queue to empty
    ##while not workQueue.empty():

        #pass

    # Notify threads it's time to exit
    #exitFlag = 1

    # Wait for all threads to complete
    #for t in threads:
    #    t.is_alive()
    #    t.join()
    #print "Exiting Main Thread"
