import xbmc
import xbmcplugin

import re
import sys

try:
    from urllib.parse import parse_qsl
    from urllib.parse import quote_plus
except ImportError:
    from urlparse import parse_qsl
    from urllib import quote_plus
    
from resources.lib import backup
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

path_pattern = '\&path=%22(.*)%22'


def _log_params(_plugin, _handle, _params):
    path_param = re.search(path_pattern, _params)
    if path_param:
        _params = re.sub(path_pattern, '&path={}'.format(quote_plus(path_param.groups()[0])),
                         _params)
    params = dict(parse_qsl(_params))
    logstring = ''
    
    for param in params:
        logstring += '[ {0}: {1} ] '.format(param, params[param])
    
    if not logstring:
        logstring = '[ Root Menu ]'

    utils.log(logstring, level=xbmc.LOGNOTICE)

    return params
    
    
def dispatch(_plugin, _handle, _params):
    _handle = int(_handle)
    params = _log_params(_plugin, _handle, _params)
    category = 'AutoWidget'
    is_dir = False
    is_type = 'files'

    utils.ensure_addon_data()
    
    mode = params.get('mode', '')
    action = params.get('action', '')
    group = params.get('group', '')
    path = params.get('path', '')
    target = params.get('target', '')
    _id = params.get('id', '')
    
    if not mode:
        is_dir, category = menu.root_menu()
    elif mode == 'manage':
        if action == 'add_group':
            manage.add_group(target)
        elif action == 'add_path' and group and target:
            manage.add_path(group, target)
        elif action == 'shift_path' and group and path and target:
            edit.shift_path(group, path, target)
        elif action == 'edit':
            edit.edit_dialog(group, path)
        elif action == 'edit_widget':
            edit.edit_widget_dialog(target)
    elif mode == 'path':
        if action == 'call' and group and path:
            menu.call_path(group, path)
        elif action in ['random', 'next'] and group:
            is_dir, category = menu.path_menu(group, action, _id, path)
        elif action == 'merged' and group:
            is_dir, category = menu.merged_path(group, _id)
            is_type = 'videos'
        elif action == 'update' and path and target:
            menu.update_path(_id, path, target)
    elif mode == 'group':
        if not group:
            is_dir, category = menu.my_groups_menu()
        elif target:
            is_dir, category = menu.group_menu(group, target, _id)
    elif mode == 'widget':
        is_dir, is_category = menu.active_widgets_menu()
    elif mode == 'refresh':
        if not target:
            refresh.refresh_paths()
        else:
            refresh.refresh(target, force=True)
            utils.update_container()
    elif mode == 'tools':
        is_dir, category = menu.tools_menu()
    elif mode == 'force':
        refresh.refresh_paths(notify=True, force=True)
    elif mode == 'wipe':
        utils.wipe()
    elif mode == 'clean':
        manage.clean()
    elif mode == 'backup' and action:
        if action == 'location':
            backup.location()
        elif action == 'backup':
            backup.backup()
        elif action == 'restore':
            backup.restore()

    if is_dir:
        directory.add_sort_methods(_handle)
        xbmcplugin.setPluginCategory(_handle, category)
        xbmcplugin.setContent(_handle, is_type)
        xbmcplugin.endOfDirectory(_handle)
