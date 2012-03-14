import urwid
import malconstrict.malapi

class StatusItemWidget (urwid.WidgetWrap):
    def __init__ (self, message):
        self.id = id
        self.title = urwid.Text('Status')
        self.description = urwid.Text(message)
        self.item = [
            (
                'fixed',
                15,
                urwid.Padding(urwid.AttrWrap( self.title, 'body', 'focus'), left=2)
            ),
            urwid.AttrWrap(self.description, 'body', 'focus'),
        ]
        self.content = message
        w = urwid.Columns(self.item)
        self.__super.__init__(w)

    def selectable (self):
        return False

    def keypress(self, size, key):
        return key


class ItemWidget (urwid.WidgetWrap):
    def __init__ (self, id, description):
        self.id = id
        self.title = urwid.Text('item %s' % str(id))
        self.description = urwid.Text(description)
        self.item = [
            ('fixed', 15, urwid.Padding(urwid.AttrWrap( self.title, 'body', 'focus'), left=2)),
            urwid.AttrWrap(self.description, 'body', 'focus'),
        ]
        self.content = 'item ' + str(id)
        w = urwid.Columns(self.item)
        self.__super.__init__(w)

    def selectable (self):
        return True

    def keypress(self, size, key):
        return key



class LoginWidget(urwid.Edit):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['login_authenticate', 'login_escaped']
    
    def __init__(self, prompt):
        self.username_in = False
        self.password_in = False
        self.username = ''
        self.password = ''
        urwid.Edit.__init__(self, prompt)

    def keypress(self, size, key):
        if key == 'enter':
            if not self.username_in:
                self.username = self.get_edit_text()
                self.username_in = True
                self.set_edit_text('')
                self.set_caption('password >> ')
            elif not self.password_in:
                self.password = self.get_edit_text()
                self.password_in = True
                self.set_caption('authenticating...')
                urwid.emit_signal(
                    self, 'login_authenticate', (self.username, self.password))
                return
        elif key == 'esc':
            self.username = ''
            self.password = ''
            self.username_in = False
            self.password_in = False
            urwid.emit_signal(self, 'login_escaped', None)
            return

        urwid.Edit.keypress(self, size, key)


class MyApp(object):
    def __init__(self):
        self.username = ''
        self.password = ''
        
        # defines the color palette of the main window
        palette = [
                    ('body','dark blue', '', 'standout'),
                    ('focus','dark red', '', 'standout'),
                    ('head','light red', 'black'),
                    ]
        
        self.header = urwid.AttrMap(urwid.Text('MALSnakes v0.1 - not logged in!'), 'head')
        self.default_footer = urwid.AttrMap(urwid.Text("l - login      v - view selection details      p - pull in user's list      q - quit"), 'head')
        
        items = []
        items.append(StatusItemWidget('Nothing to view.'))
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view = urwid.Frame(
                urwid.AttrWrap(self.listbox, 'body'),
                header=self.header,
                footer=self.default_footer
        )
        
        loop = urwid.MainLoop(
            self.view, palette, unhandled_input=self.uncaught_keystroke)
        urwid.connect_signal(walker, 'modified', self.update)
        loop.run()
    
    
    def pull_in_list(self):
        lst = malconstrict.malapi.get_anime_list(self.username)
        items = []
        i = 0
        for anime in lst.anime:
            items.append(ItemWidget(i, anime.title))
            i = i + 1
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
    
    
    def update(self):
        focus = self.listbox.get_focus()[0].content
        self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'head'))
    
    
    def uncaught_keystroke(self, data):
        if data is 'down':
            self.listbox.keypress([0, 1], 'down')
        elif data is 'up':
            self.listbox.keypress([0, 1], 'up')
        elif data is 'q':
            raise urwid.ExitMainLoop()
        if data is 'enter':
            focus = self.listbox.get_focus()[0].content
            self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'head'))
        if data is 'l':
            self.login()
    
    def login(self):
        self.foot = LoginWidget('username >> ')
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(
            self.foot, 'login_authenticate', self.login_authenticate)
        urwid.connect_signal(self.foot, 'login_escaped', self.login_escaped)
    

    def login_authenticate(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'login_authenticate', self.login_authenticate)
        urwid.disconnect_signal(
            self, self.foot, 'login_escaped', self.login_escaped)
        self.username = content[0]
        self.password = content[1]
        self.view.set_footer(self.default_footer)
        self.view.set_header(urwid.AttrMap(
                urwid.Text('[Logged In] Viewing your list'), 'head'))
        self.pull_in_list()
    
    
    def login_escaped(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'login_authenticate', self.login_authenticate)
        urwid.disconnect_signal(
            self, self.foot, 'login_escaped', self.login_escaped)
        self.username = ''
        self.password = ''
        self.view.set_footer(self.default_footer)
    


if __name__ == '__main__':
    MyApp()