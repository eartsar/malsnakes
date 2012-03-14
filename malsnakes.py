import urwid
import malconstrict.malapi



############# WIDGET CLASSES ##############


class StatusItemWidget (urwid.WidgetWrap):
    def __init__ (self, message):
        self.id = id
        self.title = urwid.Text('Status')
        self.description = urwid.Text(message)
        self.item = [
            (
                'fixed',
                15,
                urwid.Padding(urwid.AttrWrap( self.title, 'body', 'body'), left=2)
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
        self.title = urwid.Text(str(id))
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



class QueryWidget(urwid.Edit):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['username_entered',
                'anime_entered',
                'search_entered',
                'query_escaped']

    def __init__(self, prompt):
        self.prompt = prompt
        urwid.Edit.__init__(self, prompt)

    def keypress(self, size, key):
        if key == 'enter':
            if self.prompt == 'anime title: ':
                urwid.emit_signal(
                    self,
                    'anime_entered',
                    self.get_edit_text(),
                )
                return
            elif self.prompt == 'username: ':
                urwid.emit_signal(
                    self,
                    'username_entered',
                    self.get_edit_text(),
                )
                return
            elif self.prompt == 'search: ':
                urwid.emit_signal(
                    self,
                    'search_entered',
                    self.get_edit_text(),
                )
                return
        elif key == 'esc':
            urwid.emit_signal(self, 'query_escaped', None)
            return

        urwid.Edit.keypress(self, size, key)



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
                self.set_caption('password: ')
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



############# MAIN APP CLASS ###############



class MyApp(object):
    def __init__(self):
        self.username = ''
        self.password = ''
        self.cached_list = []
        self.cached_anime = None
        self.authenticated = False
        
        # defines the color palette of the main window
        palette = [
                    ('body','dark blue', '', 'standout'),
                    ('focus','black', 'light blue', 'standout'),
                    ('head','light red', 'black'),
                    ('foot','light blue', 'black'),
                    ]
        
        # The header bar of the window
        self.header = urwid.AttrMap(urwid.Text('MALSnakes - not logged in!'), 'head')
        # The default footer bar of the window
        self.default_footer = urwid.AttrMap(urwid.Text("l - login      r - pull yours      p - pull other's      v - view selection      s - search list      q - quit"), 'foot')
        
        # The default items to be displayed (prior to authentication)
        items = []
        items.append(StatusItemWidget('Nothing to view.'))
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view = urwid.Frame(
                urwid.AttrWrap(self.listbox, 'body'),
                header=self.header,
                footer=self.default_footer
        )
        
        # launch the main app loop for urwid
        loop = urwid.MainLoop(
            self.view, palette, unhandled_input=self.uncaught_keystroke)
        urwid.connect_signal(walker, 'modified', self.update)
        loop.run()


    def update(self):
        focus = self.listbox.get_focus().content
        self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'focus'))
    
    
    def uncaught_keystroke(self, data):
        if data is 'down':
            self.listbox.keypress([0, 1], 'down')
        elif data is 'up':
            self.listbox.keypress([0, 1], 'up')
        elif data is 'q':
            raise urwid.ExitMainLoop()
        elif data is 'p':
            self.query_username()
        elif data is 'a':
            self.query_anime()
        elif data is 's':
            self.search_list()
        elif data is 'v':
            return
        elif data is 'r':
            self.refresh_own_list()
        if data is 'enter':
            focus = self.listbox.get_focus()[0].content
            self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'head'))
        if data is 'l':
            self.login()



    ############# METHODS CALLED VIA KEYSTROKES ###############
    def refresh_own_list(self):
        if not self.authenticated:
            items = []
            items.append(StatusItemWidget('You must log in to view your list.'))
            walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(walker)
            self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
            return
        else:
            self.pull_in_list(self.username)


    def pull_in_list(self, username):
        """Pulls in a user's list."""

        tmp_items = []
        tmp_items.append(StatusItemWidget('Loading...'))
        walker = urwid.SimpleListWalker(tmp_items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        
        lst = malconstrict.malapi.get_anime_list(username)
        cached_list = lst
        items = []
        i = 1
        for anime in lst.anime:
            items.append(ItemWidget(i, anime.title))
            i = i + 1
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_focus('body')
        
        if username == self.username:
            self.view.set_header(urwid.AttrMap(
                    urwid.Text('MALSnakes - viewing your list'),
                    'head'))
        else:
            self.view.set_header(urwid.AttrMap(
                    urwid.Text('MALSnakes - viewing ' + username + "'s list"),
                    'head'))


    def login(self):
        self.foot = LoginWidget('username: ')
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(
            self.foot, 'login_authenticate', self.login_authenticate)
        urwid.connect_signal(self.foot, 'login_escaped', self.login_escaped)
    
    
    def query_username(self):
        self.foot = QueryWidget('username: ')
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(
            self.foot, 'username_entered', self.username_entered)
        urwid.connect_signal(self.foot, 'query_escaped', self.query_escaped)


    def query_anime(self):
        self.foot = QueryWidget('anime title: ')
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(
            self.foot, 'anime_entered', self.username_entered)
        urwid.connect_signal(self.foot, 'query_escaped', self.query_escaped)
    

    def search_list(self):
        self.foot = QueryWidget('search: ')
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(
            self.foot, 'search_entered', self.search_entered)
        urwid.connect_signal(self.foot, 'query_escaped', self.query_escaped)
    


    ############# METHODS CALLED VIA SIGNAL CALLBACK ###############


    def login_authenticate(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'login_authenticate', self.login_authenticate)
        urwid.disconnect_signal(
            self, self.foot, 'login_escaped', self.login_escaped)
        self.username = content[0]
        self.password = content[1]
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_header(urwid.AttrMap(
                urwid.Text('MALSnakes - logged in as ' + self.username), 'head'))
        self.authenticated = True
    
    
    def login_escaped(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'login_authenticate', self.login_authenticate)
        urwid.disconnect_signal(
            self, self.foot, 'login_escaped', self.login_escaped)
        self.username = ''
        self.password = ''
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
    
    
    def query_escaped(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'username_entered', self.username_entered)
        urwid.disconnect_signal(
            self, self.foot, 'anime_entered', self.anime_entered)
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
    
    
    def username_entered(self, content):
        self.pull_in_list(content)
    
    
    def anime_entered(self, content):
        return
    
    
    def search_entered(self, content):
        return
    
    


if __name__ == '__main__':
    MyApp()