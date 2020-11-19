#!/usr/bin/env python3
#
# Simple AppIndicator which uses the HeadsetControl application from
# https://github.com/Sapd/HeadsetControl/ for retrieving charge information
# for wireless headsets and displays it as app-indicator
#
#
# Simple start this application as background process, i.e. during
# startup of the graphical desktop

from sys import argv

from gi import require_version

require_version('Gtk', '3.0')
require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator
from subprocess import check_output, CalledProcessError

APPINDICATOR_ID = 'headset-charge-indicator'

global HEADSETCONTROL_BINARY
HEADSETCONTROL_BINARY = None

global SWITCHSOUND_BINARY
SWITCHSOUND_BINARY = None

OPTION_BATTERY = '-b'
OPTION_SILENT = '-c'
OPTION_CHATMIX = '-m'
OPTION_SIDETONE = '-s'
OPTION_LED = '-l'

global ind
ind = None
global chatmix
chatmix = None
global charge
charge = None
global prevSwitch
prevSwitch = 0


def change_icon(dummy):
    global prevSwitch
    try:
        output = check_output([SWITCHSOUND_BINARY, "-1"])
        # only
        if prevSwitch == 0:
            # exit 0 means we could not find out, so set some other icon
            ind.set_attention_icon_full("audio-card", "Audio Card")
    except CalledProcessError as e:
        print(e)
        if e.returncode == 1:
            ind.set_attention_icon_full("audio-speakers", "Audio Card")
            prevSwitch = 1
        elif e.returncode == 2:
            ind.set_attention_icon_full("audio-headset", "Headset")
            prevSwitch = 2
        elif e.returncode == 3:
            ind.set_attention_icon_full("audio-headphones", "USB")
            prevSwitch = 3
        else:
            ind.set_attention_icon_full("audio-input-microphone", "Speakerphone")
            prevSwitch = 4

    return True


def change_label(dummy):
    try:
        output = check_output([HEADSETCONTROL_BINARY, OPTION_BATTERY, OPTION_SILENT])
        print('Bat: ' + str(output, 'utf-8'))
        # -1 indicates "Battery is charging"
        if int(output) == -1:
            ind.set_label('Chg', '999%')
            ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        # -2 indicates "Battery is unavailable"
        elif int(output) == -2:
            ind.set_label('Off', '999%')
            ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        elif int(output) < 100:
            ind.set_label(str(output, 'utf-8') + '%', '999%')
            ind.set_status(appindicator.IndicatorStatus.ATTENTION)
        else:
            ind.set_label(str(output, 'utf-8') + '%', '999%')
            ind.set_status(appindicator.IndicatorStatus.ACTIVE)
    except CalledProcessError as e:
        print(e)
        ind.set_label('N/A', '999%')

    return True


def change_chatmix(dummy):
    global chatmix

    try:
        output = check_output([HEADSETCONTROL_BINARY, OPTION_CHATMIX, OPTION_SILENT])
        print("ChatMix: " + str(output, 'utf-8'))
        chatmix.get_child().set_text('ChatMix: ' + str(output, 'utf-8'))
    except CalledProcessError as e:
        print(e)
        chatmix.get_child().set_text('ChatMix: N/A')

    return True


def show_charge(dummy):
    global charge

    try:
        output = check_output([HEADSETCONTROL_BINARY, OPTION_BATTERY, OPTION_SILENT])
        print("Battery: " + str(output, 'utf-8'))
        if int(output) == -1:
            charge.get_child().set_text('Charging')
        elif int(output) == -2:
            charge.get_child().set_text('Unavailable')
        else:
            charge.get_child().set_text('Charge: ' + str(output, 'utf-8') + '%')
    except CalledProcessError as e:
        print(e)
        charge.get_child().set_text('N/A')
    return True


def set_sidetone(dummy, level):
    print("Set sidetone to: " + str(level))
    try:
        output = check_output([HEADSETCONTROL_BINARY, OPTION_SIDETONE, str(level), OPTION_SILENT])
        print("Result: " + str(output, 'utf-8'))
    except CalledProcessError as e:
        print(e)

    return True


def set_led(dummy, level):
    print("Set LED to: " + str(level))
    try:
        output = check_output([HEADSETCONTROL_BINARY, OPTION_LED, str(level), OPTION_SILENT])
        print("Result: " + str(output, 'utf-8'))
    except CalledProcessError as e:
        print(e)

    return True


def switch_sound(dummy, level):
    print("Switch sound to: " + str(level))
    try:
        output = check_output([SWITCHSOUND_BINARY, str(level)])
        print("Result: " + str(output, 'utf-8'))
    except CalledProcessError as e:
        print(e)

    # refresh UI after switching
    refresh(None)

    return True


def sidetone_menu():
    # we map 5 levels to the range of [0-128]
    # The Steelseries Arctis internally supports 0-0x12, i.e. 0-18
    #    OFF -> 0
    #    LOW -> 32
    #    MEDIUM -> 64
    #    HIGH -> 96
    #    MAX -> 128

    sidemenu = Gtk.Menu()

    off = Gtk.MenuItem(label="off")
    off.connect("activate", set_sidetone, 0)
    sidemenu.append(off)
    off.show_all()

    low = Gtk.MenuItem(label="low")
    low.connect("activate", set_sidetone, 32)
    sidemenu.append(low)
    low.show_all()

    medium = Gtk.MenuItem(label="medium")
    medium.connect("activate", set_sidetone, 64)
    sidemenu.append(medium)
    medium.show_all()

    high = Gtk.MenuItem(label="high")
    high.connect("activate", set_sidetone, 96)
    sidemenu.append(high)
    high.show_all()

    maximum = Gtk.MenuItem(label="max")
    maximum.connect("activate", set_sidetone, 128)
    sidemenu.append(maximum)
    maximum.show_all()

    return sidemenu


def led_menu():
    ledmenu = Gtk.Menu()

    off = Gtk.MenuItem(label="off")
    off.connect("activate", set_led, 0)
    ledmenu.append(off)
    off.show_all()

    on = Gtk.MenuItem(label="on")
    on.connect("activate", set_led, 1)
    ledmenu.append(on)
    on.show_all()

    return ledmenu


def switch_menu():
    switchmenu = Gtk.Menu()

    laptop = Gtk.MenuItem(label="Soundcard")
    laptop.connect("activate", switch_sound, 1)
    switchmenu.append(laptop)
    laptop.show_all()

    headset = Gtk.MenuItem(label="Headset")
    headset.connect("activate", switch_sound, 2)
    switchmenu.append(headset)
    headset.show_all()

    usb = Gtk.MenuItem(label="USB Headset")
    usb.connect("activate", switch_sound, 3)
    switchmenu.append(usb)
    usb.show_all()

    usb = Gtk.MenuItem(label="Chat Device")
    usb.connect("activate", switch_sound, 4)
    switchmenu.append(usb)
    usb.show_all()

    return switchmenu


def refresh(dummy):
    # change_label(None)
    show_charge(None)
    change_chatmix(None)
    if len(argv) == 3:
        change_icon(None)


def quit(source):
    Gtk.main_quit()


if __name__ == "__main__":
    if len(argv) != 2 and len(argv) != 3:
        print(
            "Need one or two commandline arguments, one for the location of the HeadsetControl binary and one for the optional command to switch between Laptop and Headset")
        exit(1)

    HEADSETCONTROL_BINARY = argv[1]
    if len(argv) == 3:
        SWITCHSOUND_BINARY = argv[2]

    ind = appindicator.Indicator.new(
        APPINDICATOR_ID,
        "audio-headset",
        appindicator.IndicatorCategory.HARDWARE)
    ind.set_status(appindicator.IndicatorStatus.ACTIVE)
    ind.set_label("-1%", '999%')

    # create a menu with an Exit-item
    menu = Gtk.Menu()
    menu_items = Gtk.MenuItem(label="On cable")
    menu.append(menu_items)
    menu_items.show_all()
    charge = menu_items

    menu_items = Gtk.MenuItem(label="Refresh")
    menu.append(menu_items)
    menu_items.connect("activate", refresh)
    menu_items.show_all()

    menu_items = Gtk.MenuItem(label="Chat: -1")
    menu.append(menu_items)
    menu_items.show_all()
    chatmix = menu_items

    menu_items = Gtk.MenuItem(label="Sidetone")
    menu.append(menu_items)
    menu_items.show_all()
    menu_items.set_submenu(sidetone_menu())

    menu_items = Gtk.MenuItem(label="LED")
    menu.append(menu_items)
    menu_items.show_all()
    menu_items.set_submenu(led_menu())

    if len(argv) == 3:
        menu_items = Gtk.MenuItem(label="Switch")
        menu.append(menu_items)
        menu_items.show_all()
        menu_items.set_submenu(switch_menu())

    menu_items = Gtk.MenuItem(label="Exit")
    menu.append(menu_items)
    menu_items.connect("activate", quit)
    menu_items.show_all()

    ind.set_menu(menu)

    # if we have switchSound binary, we can try to detect current output
    if len(argv) == 3:
        GLib.timeout_add(60000, change_icon, None)

    # update printed charge every 60 seconds
    GLib.timeout_add(60000, change_label, None)
    GLib.timeout_add(60000, show_charge, None)
    GLib.timeout_add(60000, change_chatmix, None)

    # refresh values right away
    refresh(None)

    Gtk.main()
