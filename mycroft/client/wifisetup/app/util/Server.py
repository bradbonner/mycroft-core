from wpaCLITools import wpaClientTools
from app.util.LinkUtils import ScanForAP
from mycroft.util.log import getLogger
import ast
import re
import tornado.websocket
import time


LOGGER = getLogger("WiFiSetupClient")


class APConfig():
    def __init__(self):
        file_template = 'config.templates/etc/hostapd/hostapd.conf.template'
        file_path = '/etc/hostapd/hostapd.conf'
        interface = 'wlan0'
        driver = 'nl80211'
        ssid = 'PI3-AP'
        hw_mode = 'g'
        channel = 6
        country_code = 'US'
        ieee80211n = 1
        wmm_enabled = 1
        ht_capab = '[HT40][SHORT-GI-20][DSSS_CCK-40]'
        macaddr_acl = 0
        ignore_broadcast_ssid = 0

    def write_config(self):
        ha.set_ssid(APConf, self.ssid)
        APConf.write()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.client_iface = 'wlan0'
        apScan = ScanForAP('scan', self.client_iface)
        apScan.start()
        apScan.join()
        self.ap = apScan.join()
        self.render("index.html", ap=self.ap)


class JSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info("request for jquery.min.js")
        self.render("jquery-2.2.3.min.js")


class BootstrapMinJSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info("request for bootstrap,min.js")
        self.render("bootstrap-3.3.7-dist/js/bootstrap.min.js")


class BootstrapMinCSSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info("request for bootstrap.min.css")
        self.render("bootstrap-3.3.7-dist/css/bootstrap.min.css")


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        LOGGER.info('a user is connected')

    def on_message(self, message):
        LOGGER.info('received message: %s\n' % message)
        self.write_message(message + ' OK')
        self.message_switch(message)

    def on_close(self):
        LOGGER.info('connection closed\n')

    def is_match(self, regex, text):
        self.pattern = re.compile(regex)
        return self.pattern.search(text) is not None

    def message_switch(self, message):
        self.client_iface = 'wlan0'
        self.ap_iface = 'uap0'
        self.dict2 = ast.literal_eval(message)
        LOGGER.info(type(self.dict2))
        if self.is_match("'ap_on'", message) is True:
            station_mode_on()
        elif self.is_match("'ap_off'", message) is True:
            station_mode_off()
        elif self.is_match("'scan_networks'", message) is True:
            LOGGER.info("Need: Refresh page/div/unhide/something")
        elif self.is_match("'ssid'", message) is True:
            LOGGER.info("SSID selected: ", self.dict2['ssid'])
            wifi_connection_settings['ssid'] = self.dict2['ssid']
        elif self.is_match("'passphrase'", message) is True:
            LOGGER.info("PASSPHRASE Recieved:", self.dict2)
            LOGGER.info(self.dict2['passphrase'])
            wifi_connection_settings['passphrase'] = self.dict2['passphrase']
            ssid = wifi_connection_settings['ssid']
            passphrase = self.dict2['passphrase']
            ssid = '''"''' + ssid + '''"'''
            passphrase = '''"''' + passphrase + '''"'''
            WiFi = wpaClientTools()
            network_id = WiFi.wpa_cli_add_network(
                self.client_iface)['stdout'].strip()
            LOGGER.info(network_id)
            LOGGER.info(WiFi.wpa_cli_set_network(
                self.client_iface, str(network_id), 'ssid', ssid))
            LOGGER.info(WiFi.wpa_cli_set_network(
                self.client_iface, str(network_id), 'psk', passphrase))
            LOGGER.info(WiFi.wpa_cli_enable_network(
                self.client_iface, network_id))
            x = 15
            while x > 0:
                try:
                    if WiFi.wpa_cli_status(
                            self.client_iface)['wpa_state'] == 'COMPLETED':
                        LOGGER.info("CONNECTED")
                        self.write_message("Authenication Sucessful")
                        LOGGER.info(
                            WiFi.wpa_save_network(str(network_id)))
                        self.write_message(
                            "Saving Network SSID and Passphrase")
                        LOGGER.info(
                            WiFi.wpa_cli_disable_network(str(network_id)))
                        x = 0
                except:
                    self.write_message("Attempting to Authenticate")
                    LOGGER.info("Attemping to Authenticate")
                    x -= 1
                    time.sleep(1)