import xbmc
import xbmcgui

import random
import re
import uuid

import six

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

add = utils.get_art('add')
alert = utils.get_art('alert')
back = utils.get_art('back')
folder = utils.get_art('folder')
folder_shortcut = utils.get_art('folder-shortcut')
folder_sync = utils.get_art('folder-sync')
folder_next = utils.get_art('folder-next')
folder_merged = utils.get_art('folder-dots')
info = utils.get_art('information_outline')
merge = utils.get_art('merge')
next = utils.get_art('next')
next_page = utils.get_art('next_page')
refresh_art = utils.get_art('refresh')
remove = utils.get_art('remove')
share = utils.get_art('share')
shuffle = utils.get_art('shuffle')
sync = utils.get_art('sync')
tools = utils.get_art('tools')
unpack = utils.get_art('unpack')


def root_menu():
    directory.add_menu_item(title=32007,
                            params={'mode': 'group'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title=32074,
                            params={'mode': 'widget'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title=32008,
                            params={'mode': 'tools'},
                            art=tools,
                            isFolder=True)
                            
    return True, 'AutoWidget'
                            
                            
def my_groups_menu():
    groups = manage.find_defined_groups()
    if len(groups) > 0:
        for group in groups:
            _id = uuid.uuid4()
            group_name = group['label']
            group_id = group['id']
            group_type = group['type']
            
            cm = [(utils.get_string(32061),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=edit'
                   '&group={})').format(group_id))]
            
            directory.add_menu_item(title=group_name,
                                    params={'mode': 'group',
                                            'group': group_id,
                                            'target': group_type,
                                            'id': six.text_type(_id)},
                                    info=group.get('info', {}),
                                    art=group.get('art') or (folder_shortcut
                                                             if group_type == 'shortcut'
                                                             else folder_sync),
                                    cm=cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32068,
                                art=alert,
                                isFolder=False,
                                props={'specialsort': 'bottom'})
                                
    return True, utils.get_string(32007)
    
    
def group_menu(group_id, target, _id):
    _window = utils.get_active_window()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'
                  .format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group['label']
    
    paths = manage.find_defined_paths(group_id)
    if len(paths) > 0:
        cm = []
        art = folder_shortcut if target == 'shortcut' else folder_sync
        
        for idx, path_def in enumerate(paths):
            if _window == 'media':
                cm = _create_context_items(group_id, path_def['id'], idx,
                                           len(paths))
            
            directory.add_menu_item(title=path_def['label'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'group': group_id,
                                            'path': path_def['id']},
                                    info=path_def['file'],
                                    art=path_def['file']['art'] or art,
                                    cm=cm,
                                    isFolder=False)
                                    
        if target == 'widget' and _window != 'home':
            directory.add_separator(title=32010, char='/', sort='bottom')

            path_param = '$INFO[Window(10000).Property(autowidget-{}-action)]'.format(_id)

            directory.add_menu_item(title=utils.get_string(32076)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'static',
                                            'group': group_id,
                                            'id': six.text_type(_id),
                                            'path': path_param},
                                    art=folder,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
            directory.add_menu_item(title=utils.get_string(32028)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'cycling',
                                            'group': group_id,
                                            'id': six.text_type(_id),
                                            'path': path_param},
                                    art=shuffle,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
            directory.add_menu_item(title=utils.get_string(32089)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'merged',
                                            'group': group_id,
                                            'id': six.text_type(_id)},
                                    art=merge,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False,
                                props={'specialsort': 'bottom'})
    
    return True, group_name
    
    
def active_widgets_menu():
    widgets = manage.find_defined_widgets()
    
    if len(widgets) > 0:
        for widget_def in widgets:
            _id = widget_def.get('id', '')
            action = widget_def.get('action', '')
            group = widget_def.get('group', '')
            path_def = widget_def.get('path', {})
            updated = widget_def.get('updated', '')
            
            if action not in ['random', 'next']:
                continue
            
            group_def = manage.get_group_by_id(group)
            
            title = ''
            if path_def and group_def:
                try:
                    if isinstance(path_def, dict):
                        label = path_def['label'].encode('utf-8')
                    else:
                        label = widget_def['stack'][0]['label'].encode('utf-8')
                    group_def['label'] = group_def['label'].encode('utf-8')
                except:
                    pass
                
                title = '{} - {}'.format(label, group_def['label'])
            elif group_def:
                title = group_def.get('label')

            art = {}
            params = {}
            if not action:
                art = folder_shortcut
                params = {'mode': 'group',
                          'group': group,
                          'target': 'shortcut',
                          'id': six.text_type(_id)}
                title = utils.get_string(32030).format(title)
            elif action in ['random', 'next']:
                if action == 'random':
                    art = folder_sync
                elif action == 'next':
                    art = folder_next
                
                params = {'mode': 'group',
                          'group': group,
                          'target': 'widget',
                          'id': six.text_type(_id)}
                
            cm = [(utils.get_string(32069), ('RunPlugin('
                                            'plugin://plugin.program.autowidget/'
                                            '?mode=refresh'
                                            '&target={})').format(_id)),
                  (utils.get_string(32070), ('RunPlugin('
                                            'plugin://plugin.program.autowidget/'
                                            '?mode=manage'
                                            '&action=edit_widget'
                                            '&target={})').format(_id))]
            
            if not group_def:
                title = '{} - [COLOR firebrick]{}[/COLOR]'.format(_id, utils.get_string(32071))
                
            directory.add_menu_item(title=title,
                                    art=art,
                                    params=params,
                                    cm=cm[1:] if not action else cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32072,
                                art=alert,
                                isFolder=False,
                                props={'specialsort': 'bottom'})

    return True, utils.get_string(32074)
    
    
def tools_menu():
    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=refresh_art,
                            info={'plot': utils.get_string(32020)},
                            isFolder=False)
    directory.add_menu_item(title=32064,
                            params={'mode': 'wipe'},
                            art=remove,
                            isFolder=False)
                            
    return True, utils.get_string(32008)


def show_path(group_id, path_id, path_label, _id, titles=None, num=1, merged=False):
    hide_watched = utils.get_setting_bool('widgets.hide_watched')
    show_next = utils.get_setting_int('widgets.show_next')
    paged_widgets = utils.get_setting_bool('widgets.paged')
    
    widget_def = manage.get_widget_by_id(_id)
    if not widget_def:
        return True, 'AutoWidget'

    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    path = path_def['file']['file'] if path_def else path_id
    
    stack = widget_def.get('stack', [])
    if stack:
        title = utils.get_string(32110).format(len(stack))
        directory.add_menu_item(title=title,
                                params={'mode': 'path',
                                        'action': 'update',
                                        'id': _id,
                                        'path': stack[-1],
                                        'target': 'back'},
                                art=back,
                                isFolder=num > 1,
                                props={'specialsort': 'top',
                                       'autoLabel': path_label})
    
    if not titles:
        titles = []

    files = utils.get_files_list(path, titles)
    if not files:
        return titles, path_label
        
    for file in files:
        properties = {'autoLabel': path_label}
        if 'customproperties' in file:
            for prop in file['customproperties']:
                properties[prop] = file['customproperties'][prop]
        
        next_item = re.sub('[^\w \xC0-\xFF]',
                           '', file['label'].lower()).strip() in ['next',
                                                                  'next page']
        prev_item = re.sub('[^\w \xC0-\xFF]',
                           '', file['label'].lower()).strip() in ['previous',
                                                                  'previous page',
                                                                  'back']
        
        if (prev_item and stack) or (next_item and show_next == 0):
            continue
        elif next_item and show_next > 0:
            label = utils.get_string(32111)
            properties['specialsort'] = 'bottom'
            
            if num > 1:
                if show_next == 1:
                    continue
                    
                label = '{} - {}'.format(label, path_label)

            update_params = {'mode': 'path',
                             'action': 'update',
                             'id': _id,
                             'path': file['file'],
                             'target': 'next'}

            directory.add_menu_item(title=label,
                                    params=update_params if paged_widgets and not merged else None,
                                    path=file['file'] if not paged_widgets or merged else None,
                                    art=next_page,
                                    info=file,
                                    isFolder=not paged_widgets or merged,
                                    props=properties)
        else:
            if hide_watched and file.get('playcount', 0) > 0:
                continue
        
            directory.add_menu_item(title=file['label'],
                                    path=file['file'],
                                    art=file['art'],
                                    info=file,
                                    isFolder=file['filetype'] == 'directory',
                                    props=properties)
            
            titles.append(file.get('label'))
         
    return titles, path_label
    
    
def call_path(group_id, path_id):
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    if not path_def:
        return
    
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    xbmc.sleep(500)
    final_path = ''
    
    if path_def['target'] == 'shortcut' and path_def['file']['filetype'] == 'file' \
                                        and path_def['content'] != 'addons':
        if path_def['file']['file'] == 'addons://install/':
            final_path = 'InstallFromZip'
        elif path_def['content'] == 'files': 
            final_path = 'RunPlugin({})'.format(path_def['file']['file'])
        elif path_def['file']['file'].startswith('androidapp://sources/apps/'):
            final_path = 'StartAndroidActivity({})'.format(path_def['file']['file']
                                                           .replace('androidapp://sources/apps/', ''))
        elif all(i in path_def['file']['file'] for i in ['(', ')']) and '://' not in path_def['file']['file']:
            final_path = path_def['file']['file']
        else:
            final_path = 'PlayMedia({})'.format(path_def['file']['file'])
    elif path_def['target'] == 'widget' or path_def['file']['filetype'] == 'directory' \
                                        or path_def['content'] == 'addons':
        final_path = 'ActivateWindow({},{},return)'.format(path_def.get('window', 'Videos'),
                                                           path_def['file']['file'])
    elif path_def['target'] == 'settings':
        final_path = 'Addon.OpenSettings({})'.format(path_def['file']['file']
                                                     .replace('plugin://', ''))
        
    if final_path:
        xbmc.executebuiltin(final_path)
        
    return False, path_def['label']


def path_menu(group_id, action, _id, path=None):
    _window = utils.get_active_window()
    
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        directory.add_menu_item(title=32073,
                                info={'plot': utils.get_string(32075)},
                                art=alert,
                                isFolder=True)
        return True, 'AutoWidget'
        
    group_name = group_def.get('label', '')
    paths = group_def.get('paths', [])
    if len(paths) == 0:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=True)
        return True, group_name
    
    widget_def = manage.get_widget_by_id(_id, group_id)
    if widget_def and _window != 'dialog':
        path_def = widget_def['path']
    elif not widget_def:
        dialog = xbmcgui.Dialog()
        if action == 'static':
            idx = dialog.select(utils.get_string(32114), [i['label'] for i in paths])
            if idx == -1:
                return True, 'AutoWidget'
            
            widget_def = manage.initialize(group_def, action, _id, keep=idx)
        elif action == 'cycling':
            idx = dialog.select(utils.get_string(32081), [utils.get_string(32079),
                                                          utils.get_string(32080)])
            if idx == -1:
                return True, 'AutoWidget'
            
            _action = 'random' if idx == 0 else 'next'
            widget_def = manage.initialize(group_def, _action, _id)
    
    if widget_def:
        widget_path = widget_def.get('path', {})
        _path = path if path else widget_path
        
        if isinstance(widget_path, dict):
            _label = widget_path['label']
            _path = widget_path['file']['file']
        else:
            stack = widget_def.get('stack', [])
            if stack:
                _label = stack[0]['label']
            else:
                _label = widget_def.get('label', '')
        
        titles, cat = show_path(group_id, _path, _label, _id)
        return titles, cat
    else:
        directory.add_menu_item(title=32067,
                                art=info,
                                isFolder=True)
        return True, group_name
        
        
def merged_path(group_id, _id):
    _window = utils.get_active_window()
    
    group_def = manage.get_group_by_id(group_id)
    group_name = group_def.get('label', '')
    paths = group_def.get('paths', [])
    if len(paths) == 0:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
        return True, group_name
    
    widget_def = manage.get_widget_by_id(_id, group_id)
    if widget_def and _window != 'dialog':
        paths = widget_def['path']
    elif not widget_def:
        dialog = xbmcgui.Dialog()
        idxs = dialog.multiselect(utils.get_string(32115),
                                  [i['label'] for i in paths],
                                  preselect=list(range(len(paths))) if len(paths) <= 5 else [])
        if idxs is not None:
            if len(idxs) == 0:
                pass
            else:
                widget_def = manage.initialize(group_def, 'merged',
                                               _id, keep=idxs)
                paths = widget_def['path']
        
    if widget_def:
        titles = []
        for path_def in paths:
            titles, cat = show_path(group_id, path_def['id'], path_def['label'],
                                    _id, num=len(paths), merged=True)

        return titles, cat
    else:
        directory.add_menu_item(title=32067,
                                art=info,
                                isFolder=True)
        return True, group_name


def _create_context_items(group_id, path_id, idx, length):
    cm = [(utils.get_string(32048),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=edit'
               '&group={}'
               '&path={})').format(group_id, path_id)),
          (utils.get_string(32026) if idx > 0 else utils.get_string(32113),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=shift_path'
               '&target=up'
               '&group={}'
               '&path={})').format(group_id, path_id)),
          (utils.get_string(32027) if idx < length - 1 else utils.get_string(32112),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=shift_path'
               '&target=down'
               '&group={}'
               '&path={})').format(group_id, path_id))]

    return cm
