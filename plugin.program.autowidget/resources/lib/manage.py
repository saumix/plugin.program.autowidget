import xbmc
import xbmcaddon

import os
import random

from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')


def initialize(group_def, action, _id, save=True, keep=None):
    duration = utils.get_setting_float('service.refresh_duration')
    paths = group_def.get('paths', [])
    path_def = []

    if action != 'merged':
        if action == 'static' and keep is not None:
            path_idx = keep
        elif action in ['random', 'next']:
            path_idx = random.randrange(len(paths)) if action == 'random' else 0
        path_def = paths[path_idx]
    elif action == 'merged' and keep:
        for idx in keep:
            path_def.append(paths[idx])

    params = {'action': action,
              'id': _id,
              'group': group_def['id'],
              'refresh': duration,
              'path': path_def,
              'version': _addon_version}
    if save:
        save_path_details(params)

    return params


def write_path(group_def, path_def=None, update=''):
    filename = os.path.join(_addon_path, '{}.group'.format(group_def['id']))

    if path_def:
        if update:
            for path in group_def['paths']:
                if path['id'] == update:
                    group_def['paths'][group_def['paths'].index(path)] = path_def
        else:
            group_def['paths'].append(path_def)

    utils.write_json(filename, group_def)
    
    
def save_path_details(params):
    path_to_saved = os.path.join(_addon_path, '{}.widget'.format(params['id']))
    utils.write_json(path_to_saved, params)

    return params


def get_group_by_id(group_id):
    if not group_id:
        return
    
    filename = '{}.group'.format(group_id)
    path = os.path.join(_addon_path, filename)
    
    try:
        group_def = utils.read_json(path)
    except ValueError:
        utils.log('Unable to parse: {}'.format(path))
        return
    
    return group_def


def get_path_by_id(path_id, group_id=None):
    if not path_id:
        return

    for defined in find_defined_paths(group_id):
        if defined.get('id', '') == path_id:
            return defined
            
            
def get_widget_by_id(widget_id, group_id=None):
    if not widget_id:
        return
        
    for defined in find_defined_widgets(group_id):
        if defined.get('id', '') == widget_id:
            return defined
    
    
def find_defined_groups(_type=''):
    groups = []
    
    for filename in [x for x in os.listdir(_addon_path) if x.endswith('.group')]:
        path = os.path.join(_addon_path, filename)
        
        group_def = utils.read_json(path)
        if group_def:
            if _type:
                if group_def['type'] == _type:
                    groups.append(group_def)
            else:
                groups.append(group_def)

    return groups
    
    
def find_defined_paths(group_id=None):
    if group_id:
        filename = '{}.group'.format(group_id)
        path = os.path.join(_addon_path, filename)
        
        group_def = utils.read_json(path)
        if group_def:
            return group_def.get('paths', [])
    else:
        paths = []
        for group in find_defined_groups():
            paths.append(find_defined_paths(group_id=group.get('id')))
        return paths
    

def find_defined_widgets(group_id=None):
    addon_files = os.listdir(_addon_path)
    widgets = []
    
    widget_files = [x for x in addon_files if x.endswith('.widget')]
    for widget_file in widget_files:
        widget_def = utils.read_json(os.path.join(_addon_path, widget_file))
    
        if widget_def:
            if not group_id:
                widgets.append(widget_def)
            elif group_id == widget_def['group']:
                widgets.append(widget_def)
    
    return widgets
