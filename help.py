#!/usr/bin/python

# Recommended storage folders for workflows:
# Volatile:~/Library/Caches/com.runningwithcrayons.Alfred-2/Workflow Data/[bundle id]
# Non-Volatile:~/Library/Application Support/Alfred 2/Workflow Data/[bundle id]

# To any pythoners out there who may read this script: this is probably atrocious code
# but it's my first python script. Forgive me. Maybe join the github development

# Written by Shawn Patrick Rice
# Post-release help from Clinxs (https://github.com/clintxs)

from __future__ import print_function, unicode_literals

import plistlib
import os
import tempfile
import subprocess
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


TEMPLATE = os.path.join(os.path.dirname(__file__), 'template.html')

HTML = open(TEMPLATE, 'rb').read().decode('utf-8')

HOTMOD = {
    131072: "shift",
    262144: "control",
    262401: "control",  # https://github.com/shawnrice/alfred2-workflow-help/pull/2/files
    393216: "shift+control",
    524288: "option",
    655360: "shift+option",
    786432: "control+option",
    917504: "shift+control+option",
    1048576: "command",
    1179648: "shift+command",
    1310720: "control+command",
    1310985: "control+command",  # https://github.com/shawnrice/alfred2-workflow-help/pull/2/files
    1441792: "shift+control+command",
    1572864: "option+command",
    1703936: "shift+option+command",
    1835008: "control+option+command",
    1966080: "shift+control+option+command"
}

HOTARG = {
    0: "No Argument",
    1: "Selection in OS X",
    2: "OS X Clipboard Contents",
    3: "Text"
}

HOTACTION = {
    0: "Pass through to Workflow",
    1: "Show Alfred"
}


def load_workflow(dirpath):
    """Load data from workflow in ``dirpath``"""
    data = {}
    commands = []
    hotkeys = []
    plist = os.path.join(dirpath, 'info.plist')
    data['icon'] = os.path.join(dirpath, 'icon.png')
    if not os.path.exists(plist):
        raise ValueError('Not a workflow : %s' % dirpath)
    info = plistlib.readPlist(plist)
    for key in ('name', 'bundleid', 'createdby', 'disabled', 'description'):
        value = info.get(key)
        if isinstance(value, str):
            value = unicode(value, 'utf-8')
        data[key] = value
    # Commands & hotkeys
    for item in info.get('objects', []):
        config = item.get('config', {})
        if item['type'] in ('alfred.workflow.input.keyword',
                            'alfred.workflow.input.scriptfilter'):
            command = {}
            for key in ('keyword', 'text', 'subtext', 'title'):
                if key in config:
                    command[key] = config[key].decode('utf-8')
            commands.append(command)
        elif item['type'] == 'alfred.workflow.trigger.hotkey':
            hotkey = {}
            if 'hotmod' in config:
                if config['hotmod'] in HOTMOD:
                    hotkey['key'] = HOTMOD[config['hotmod']]
                    hotkey['string'] = config['hotstring']
                else:
                    hotkey['undefined'] = True
            if 'argument' in config:
                hotkey['argument'] = HOTARG[config['argument']]
            hotkeys.append(hotkey)
    data['commands'] = commands
    data['hotkeys'] = hotkeys
    return data


def workflow_html(workflow):
    """Generate HTML fragment for the workflow"""
    root = ET.Element('div', {'class': 'workflow'})
    ET.SubElement(root, 'img', {'src': workflow['icon'],
                                'class': 'icon',
                                'width': '50'})
    h2 = ET.SubElement(root, 'h2')
    h2.text = workflow['name']
    if workflow.get('bundleid'):
        ET.SubElement(h2, 'span',
                      {'class': 'bundleid'}).text = workflow['bundleid']
    else:
        ET.SubElement(h2, 'span',
                      {'class': 'bundleid error'}
                      ).text = 'NO BUNDLE ID DEFINED'
    if workflow.get('createdby'):
        ET.SubElement(root, 'p',
                      {'class': 'author'}
                      ).text = 'by %s' % workflow['createdby']
    else:
        ET.SubElement(root, 'p',
                      {'class': 'author error'}
                      ).text = 'NO CREATOR ID'
    if workflow.get('description'):
        ET.SubElement(root, 'p',
                      {'class': 'description'}).text = workflow['description']
    cmdlist = ET.SubElement(root, 'ul')
    for command in workflow.get('commands', []):
        li = ET.SubElement(cmdlist, 'li')
        if not command.get('keyword'):
            ET.SubElement(li, 'span',
                          {'class': 'error'}).text = 'No keyword defined '
        else:
            ET.SubElement(li, 'span',
                          {'class': 'keyword'}
                          ).text = command.get('keyword') + ' '
        ET.SubElement(li, 'span',
                      {'class': 'text'}).text = command.get('text', '')
        ET.SubElement(li, 'p',
                      {'class': 'subtext'}).text = command.get('subtext', '')
    for hotkey in workflow.get('hotkeys', []):
        li = ET.SubElement(cmdlist, 'li')
        if hotkey.get('undefined'):
            ET.SubElement(li, 'span',
                          {'class': 'hotkey error'}).text = 'Not defined'
        else:
            ET.SubElement(li, 'span',
                          {'class': 'hotkey'}
                          ).text = (hotkey.get('key', '') + ' ' +
                                    hotkey.get('string', ''))
    return ET.tostring(root)


def main():
    tempdir = tempfile.mkdtemp()
    helpfile = os.path.join(tempdir, 'workflow_help.html')
    workflows = []
    root = os.path.abspath('..')
    # list of directories in the

    for filename in os.listdir(root):
        p = os.path.join(root, filename)
        if os.path.isdir(p):
            try:
                workflow = load_workflow(p)
            except ValueError:
                continue
            workflows.append(workflow)

    workflows.sort(key=lambda d: d['name'])
    buffer = []
    for workflow in workflows:
        buffer.append(workflow_html(workflow))
    output = '\n'.join(buffer)
    output = HTML % dict(content=output)
    # Write to temporary HTML file
    with open(helpfile, 'wb') as file:
        file.write(output.encode('utf-8'))
    subprocess.call(['open', helpfile])
    # print(output)


if __name__ == u"__main__":
    main()
