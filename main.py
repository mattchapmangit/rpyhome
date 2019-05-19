import ujson
from main.ota_updater import OTAUpdater

config = ujson.load(open('node.json'))

def download_and_install_update_if_available():
    ota_updater = OTAUpdater('https://github.com/mattchapmangit/rpyhome.git')
    ota_updater.download_and_install_update_if_available(config['wifi_ssid'], config['wifi_password'])

def start():
    # your custom code goes here. Something like this: ...
    # from main.x import YourProject
    # project = YourProject()
    # ...
    print('starting ...')

def boot():
    download_and_install_update_if_available()
    start()


boot()
