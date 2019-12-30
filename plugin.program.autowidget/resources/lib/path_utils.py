import xbmc
import xbmcaddon
import xbmcgui

import os
import random
import six
import time
import uuid

if six.PY3:
    from urllib.parse import parse_qsl
elif six.PY2:
    from urlparse import parse_qsl

from xml.etree import ElementTree as ET

from resources.lib import window


def find_defined_groups():
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
    groups = []
    
    for filename in os.listdir(shortcut_path):
        if filename.startswith('autowidget-') and filename.endswith('.xml'):
            group_name = filename[11:-9]
            groups.append(group_name)
            
    return groups
    
    
def find_defined_paths(group):
        shortcuts = xbmcaddon.Addon('script.skinshortcuts')
        shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
        paths = []
        filename = 'autowidget-{}.DATA.xml'.format(group)
        
        tree = ET.parse(os.path.join(shortcut_path, filename))
        root = tree.getroot()
                
        for shortcut in root.findall('shortcut'):
            action = shortcut.find('action').text
            paths.append(action)
        
        return paths
        
        
def get_random_path(group, change_sec=10):
    now = time.time()
    seed = now - (now % change_sec)
    rand = random.Random(seed)
    paths = find_defined_paths(group)
    random_id = uuid.uuid4()

    return (rand.choice(paths), random_id)
    
    
def add_group():
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading='Name for Group') or ''
    
    if group_name:
        window.show_window(group_name)
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')

        
def save_path_reference(filename, action, group, id):
    addon = xbmcaddon.Addon()
    data_path = xbmc.translatePath(addon.getAddonInfo('profile'))
    
    path_to_saved = os.path.join(data_path, '{}.auto'.format(filename))
    xbmc.log(path_to_saved)
    
    with open(path_to_saved, "w") as f:
        content = '{},{},{}'.format(action, group, id)
        f.write(content)
        
        
def inject_paths():
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
    
    for filename in os.listdir(shortcut_path):
        if not filename.startswith('autowidget-') and filename.endswith('.xml'):
            file_path = os.path.join(shortcut_path, filename)
            root = ET.parse(file_path).getroot()
            
            for shortcut in root.findall('shortcut'):
                # label = shortcut.find('label')
                action = shortcut.find('action')
                
                if 'plugin.program.autowidget' in action.text:         
                    path = action.text.split('\"')[1]
                    if '?' not in path:
                        continue
                    
                    params = dict(parse_qsl(path.split('?')[1]))
                    
                    action_param = params.get('action', '')
                    group_param = params.get('group', '')
                    
                    # skin_label = 'plugin.program.autowidget-{}-label'.format(group_param)
                    
                    if action_param == 'random':
                        random_path, random_id = get_random_path(group_param)
                        skin_path = 'autowidget-{}-{}-path'.format(group_param, random_id)
                        xbmc.log('Injecting path {} into skin string {}...'.format(random_path, skin_path))
                        xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, random_path))
                        action.text = '$INFO[Skin.String({})]'.format(skin_path)
                    
                    save_path_reference(filename, action_param, group_param, random_id)
                    
                    tree = ET.ElementTree(root)
                    tree.write(file_path)
                else:
                    addon = xbmcaddon.Addon()
                    data_path = xbmc.translatePath(addon.getAddonInfo('profile'))
    
                    for reference in os.listdir(data_path):
                        if filename in reference:
                            params = []
                            
                            ref_path = os.path.join(data_path, reference)
                            with open(ref_path, "r") as f:
                                params = f.read().split(',')
                                
                            skin_path = 'autowidget-{}-{}-path'.format(params[1], params[2])
                    
                            if params[0] == 'random':
                                random_path, random_id = get_random_path(params[1])
                                skin_path = 'autowidget-{}-{}-path'.format(params[1], params[2])
                                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, random_path))
