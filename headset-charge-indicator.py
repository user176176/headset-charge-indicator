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
from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator
from subprocess import check_output, CalledProcessError

APPINDICATOR_ID = 'headset-charge-indicator'

global HEADSETCONTROL_BINARY
HEADSETCONTROL_BINARY = None

OPTION_BATTERY = '-b'
OPTION_SILENT = '-c'
OPTION_CHATMIX = '-m'

global ind
ind = None

def change_label(dummy):
    try:
        output=check_output([HEADSETCONTROL_BINARY,OPTION_BATTERY,OPTION_SILENT] )
        print('Bat: ' + str(output, 'utf-8'))
        ind.set_label(str(output, 'utf-8') + '%', '999%')
        if int(output) < 30:
            ind.set_status (appindicator.IndicatorStatus.ATTENTION)
        else:
            ind.set_status (appindicator.IndicatorStatus.ACTIVE)
    except CalledProcessError as e:
        print(e)
        ind.set_label('N/A', '999%')

    return True

def change_chatmix(menu):
    try:
        output=check_output([HEADSETCONTROL_BINARY,OPTION_CHATMIX,OPTION_SILENT] )
        print("ChatMix: " + str(output, 'utf-8'))
        menu.get_child().set_text('ChatMix: ' + str(output, 'utf-8'))
    except CalledProcessError as e:
        print(e)
        menu.get_child().set_text('N/A')

    return True

def quit(source):
    Gtk.main_quit()

if __name__ == "__main__":
  if len(argv) != 2:
    print("Need one commandline argumetn for the location of the HeadsetControl binary")
    exit(1)

  HEADSETCONTROL_BINARY = argv[1]

  ind = appindicator.Indicator.new (
                        APPINDICATOR_ID,
                        "audio-headset",
                        appindicator.IndicatorCategory.HARDWARE )
  ind.set_status (appindicator.IndicatorStatus.ACTIVE)
  # no icon found yet: ind.set_attention_icon ("indicator-messages-new")
  ind.set_label("-1%", '999%')
  
  # refresh value right away
  change_label(None)

  # create a menu with an Exit-item
  menu = Gtk.Menu()
  
  menu_items = Gtk.MenuItem("Refresh")
  menu.append(menu_items)
  menu_items.connect("activate", change_label)
  menu_items.show_all()
  
  menu_items = Gtk.MenuItem("Chat: -1")
  menu.append(menu_items)
  menu_items.show_all()
  GLib.timeout_add(60000, change_chatmix, menu_items)
  
  menu_items = Gtk.MenuItem("Exit")
  menu.append(menu_items)
  menu_items.connect("activate", quit)
  menu_items.show_all()
  
  ind.set_menu(menu)

  # update printed charge every 60 seconds
  GLib.timeout_add(60000, change_label, None)

  Gtk.main()
