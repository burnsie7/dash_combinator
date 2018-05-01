import json
import sys

from argparse import ArgumentParser
from pprint import pprint

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def combine_and_export(export_widgets, export_tvars, filename):
    all_widgets = source_widgets + export_widgets
    source_dash['widgets'] = all_widgets
    all_tvars = source_tvars + export_tvars
    source_dash['template_variables'] = all_tvars
    with open(filename, 'w') as outfile:
        json.dump(source_dash, outfile, indent=4, sort_keys=True)

def export_widgets(widgets, dash_type):
    export_widgets = []
    if dash_type == 'screenboard':
        for widget in widgets:
            title = widget.get('title_text', None) or widget.get('query', None).get('')
            w_type = widget.get('type', 'No type specified')
            if w_type == 'note':
                title = widget.get('html', 'No title or query specified')
            elif w_type == 'image':
                title = widget.get('url', 'No title or query specified')
                print("Parsing widget...")
                print("Title = {}".format(title))
                print("Type = {}".format(w_type))
                clone = query_yes_no("Would you like to clone this widget?")
                if clone:
                    export_widgets.append(widget)
    elif dash_type == 'timeboard':
        for widget in widgets:
            title = widget.get('title', None)
            if not title:
                try:
                    title = widget['definition']['requests'][0]['query']
                except KeyError:
                    title = 'No Title'
            w_type = 'Unknown'
            try:
                w_type = widget['definition']['viz']
            except KeyError:
                pass
            print("Parsing widget...")
            print("Title = {}".format(title))
            print("Type = {}".format(w_type))
            clone = query_yes_no("Would you like to clone this widget?")
            if clone:
                export_widgets.append(widget)
    return export_widgets

def export_tvars(tvars, widgets):
    export_tvars = []
    remove_tvars = []
    export_widgets = []

    for tvar in tvars:
        name = tvar.get('name', 'No name')
        prefix = tvar.get('prefix', 'No prefix')
        print("Parsing template variable...")
        print("Name = {}".format(name))
        print("Prefix = {}".format(prefix))
        clone = query_yes_no("Would you like to clone this template var?")
        if clone:
            export_tvars.append(tvar)
        else:
            remove_tvars.append(tvar)

    for widget in widgets:
        if widget.get('tile_def', None) and widget['tile_def'].get('requests', None):
            #import pdb; pdb.set_trace()
            request_list = widget['tile_def']['requests']
            request_temp = []
            request_update = []
            for req in request_list:
                qr = req['q']
                for tvar in remove_tvars:
                    name = tvar.get('name', 'No name')
                    prefix = tvar.get('prefix', 'No prefix')
                    only_var_str = '{$' + name + '}'
                    begin_str = '{$' + name + ','
                    mid_str = ',$' + name + ','
                    end_str = ',' + name + '}'
                    qr = qr.replace(only_var_str, '{}')
                    qr = qr.replace(begin_str, '{')
                    qr = qr.replace(mid_str, ',')
                    qr = qr.replace(end_str, '}')
                req['q'] = qr
                request_update.append(req)
            widget['tile_def']['requests'] = request_update

        if widget.get('query', None):
            qr = widget['query']
            for tvar in remove_tvars:
                name = tvar.get('name', 'No name')
                prefix = tvar.get('prefix', 'No prefix')
                only_var_str = '{$' + name + '}'
                begin_str = '{$' + name + ','
                mid_str = ',$' + name + ','
                end_str = ',' + name + '}'
                qr = qr.replace(only_var_str, '{}')
                qr = qr.replace(begin_str, '{')
                qr = qr.replace(mid_str, ',')
                qr = qr.replace(end_str, '}')
            widget['query'] = qr

        export_widgets.append(widget)
    print("export len {}".format(len(export_widgets)))
    return export_tvars, export_widgets

def get_max_x(widgets):
    max_x = 0
    for w in widgets:
        x = w['x']
        wd = w['width']
        if max_x < (x + wd):
            max_x = x + wd
    return max_x

def update_x(widgets, x):
    for w in widgets:
        w['x'] = w['x'] + x
        if w['y'] < 2:
            w['y'] = 0

if __name__ == '__main__':
    parser = ArgumentParser(description='Download dashboard as JSON and create new Dash from JSON')
    parser.add_argument('-s', help='Source file', required=True)
    parser.add_argument('-n', help='New file', required=True)
    parser.add_argument('-d', help='Destination File', required=True)

    args = parser.parse_args()

    source_file = args.s
    new_file = args.n
    dest_file = args.d

    source_dash = json.load(open(source_file))
    new_dash = json.load(open(new_file))
    dash_type = ''

    if source_dash.get('graphs', None):
        source_dash_type = 'timeboard'
    elif source_dash.get('widgets', None):
        source_dash_type = 'screenboard'
    else:
        print('Unable to determine board type.  Exiting.')
        exit()

    if new_dash.get('graphs', None):
        new_dash_type = 'timeboard'
    elif new_dash.get('widgets', None):
        new_dash_type = 'screenboard'
    else:
        print('Unable to determine board type.  Exiting.')
        exit()

    source_max_x = 0
    if source_dash_type == 'screenboard':
        source_widgets = source_dash['widgets']
        source_max_x = get_max_x(source_widgets)
    elif source_dash_type == 'timeboard':
        source_widgets = source_dash['graphs']

    if new_dash_type == 'screenboard':
        new_widgets = new_dash['widgets']
        update_x(new_widgets, source_max_x)
    elif new_dash_type == 'timeboard':
        new_widgets = new_dash['graphs']

    source_tvars = source_dash['template_variables']
    new_tvars = new_dash['template_variables']

    if source_dash_type == 'screenboard' and new_dash_type == 'screenboard':
        cloned_widgets = export_widgets(new_widgets, new_dash_type)
        print("cloned widgets = {}".format(cloned_widgets))
        cloned_tvars, cloned_widgets = export_tvars(new_tvars, cloned_widgets)
        print("vars len = {}".format(len(cloned_tvars)))
        print("widgets len = {}".format(len(cloned_widgets)))
        combine_and_export(cloned_widgets, cloned_tvars, dest_file)
    else:
        print("Only screenboards supported currently")
        exit()
