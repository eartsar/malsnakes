import urwid
import malconstrict.malapi



############# WIDGET CLASSES ##############
class CategoryItemWidget (urwid.WidgetWrap):
    def __init__ (self, message):
        self.id = id
        self.title = urwid.Text('CATEGORY')
        self.description = urwid.Text(message.upper())
        self.item = [
            (
                'fixed',
                15,
                urwid.Padding(urwid.AttrWrap( self.title, 'head', 'focus'), left=2)
            ),
            urwid.AttrWrap(self.description, 'head', 'focus'),
        ]
        self.content = message
        w = urwid.Columns(self.item)
        self.__super.__init__(w)

    def selectable (self):
        return False

    def keypress(self, size, key):
        return key


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


class AnimeItemWidget (urwid.WidgetWrap):
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


class ListItemWidget (urwid.WidgetWrap):
    def __init__ (self, id, description, anime_id):
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
        self.username = None
        self.password = None
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
            self.username = None
            self.password = None
            self.username_in = False
            self.password_in = False
            urwid.emit_signal(self, 'login_escaped', None)
            return

        urwid.Edit.keypress(self, size, key)



############# MAIN APP CLASS ###############



class MyApp(object):
    def __init__(self):
        self.username = None
        self.password = None
        self.cached_list = []
        self.cached_sections = {}
        self.cached_anime = None
        self.authenticated = False
        self.listowner = ''
        self.cats = ('watching', 'completed', 'dropped', 'on-hold', 'plan to watch')
        self.catfocus = 0
        self.list_sorts = ('sort: categorized by title',
                    'sort: categorized by score',
                    'sort: full by title',
                    'sort: full by score'
        )
        self.list_sort_type = 0
        self.anime_search_sorts = ('sort: by title', 'sort: by score')
        self.anime_search_sort_type = 0
        self.views = ('blank', 'personal_list', 'query_list', 'detailed_entry')
        self.current_view = 0
        
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
        self.default_footer = urwid.AttrMap(urwid.Text("l - login      r - pull yours      p - pull other's      v - view selection      s - search list\ntab - change sort      left/right - change category      , - pg up      . - pg down      q - quit"), 'foot')
        
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

    
    def display_to_top(self, message):
        self.view.set_header(urwid.AttrWrap(urwid.Text(message), 'head'))
    
    def update(self):
        focus = self.listbox.get_focus().content
        self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'focus'))
    
    
    def uncaught_keystroke(self, data):
        if data is 'down':
            self.listbox.keypress([0, 1], 'down')
        elif data is 'up':
            self.listbox.keypress([0, 1], 'up')
        elif data is 'left':
            self.change_cat_focus(back = True)
        elif data is 'right':
            self.change_cat_focus()
        elif data is 'q':
            raise urwid.ExitMainLoop()
        elif data is 'p':
            self.query_username()
        elif data is 'a':
            self.query_anime()
        elif data is 's':
            self.search_list()
        elif data is 'v':
            focus = self.listbox.get_focus()[0].content
            self.view_anime_details(focus)
        elif data is 'r':
            self.refresh_own_list()
        elif data is 'enter':
            focus = self.listbox.get_focus()[0].content
            self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(focus)), 'head'))
        elif data is 'l':
            self.login()
        elif data is 'tab':
            self.change_list_sort()
        elif data is ',':
            self.listbox.keypress([0, 10], 'page up')
        elif data is '.':
            self.listbox.keypress([0, 10], 'page down')



    ############# METHODS CALLED VIA KEYSTROKES ###############
    def view_anime_details(self, entry):
        return
    
    
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
    
    
    def change_cat_focus(self, back=False):
        if self.current_view != 1:
            return
        
        if not back:
            self.catfocus = (self.catfocus + 1) % len(self.cats)
        elif back:
            self.catfocus = (self.catfocus - 1) % len(self.cats)
        
        items = []
        if self.list_sort_type == 0 or self.list_sort_type == 1:
            i = 1
            cat_anime = self.cached_sections[self.cats[self.catfocus]]
            items.append(CategoryItemWidget(self.cats[self.catfocus]))
            for anime in cat_anime:
                items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
                i = i + 1
        elif self.list_sort_type == 2 or self.list_sort_type == 3:
            return
        
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_focus('body')
        

    def change_list_sort(self):
        if self.current_view == 0:
            return
        
        elif self.current_view == 1:
            # categorized by title -> categorized by score -> full by title -> full by score
            self.list_sort_type = (self.list_sort_type + 1) % len(self.list_sorts)
            if self.list_sort_type == 0:
                self.cached_sections = malconstrict.helpers.sort_anime_sectional(self.cached_list, how='title')
            elif self.list_sort_type == 1:
                self.cached_sections = malconstrict.helpers.sort_anime_sectional(self.cached_list, how='score', descending=True)
            elif self.list_sort_type == 2:
                malconstrict.helpers.sort_anime(self.cached_list, how='title')
            elif self.list_sort_type == 3:
                malconstrict.helpers.sort_anime(self.cached_list, how='score', descending=True)
        
            items = []
            if self.list_sort_type == 0 or self.list_sort_type == 1:
                i = 1
                cat_anime = self.cached_sections[self.cats[self.catfocus]]
                items.append(CategoryItemWidget(self.cats[self.catfocus]))
                for anime in cat_anime:
                    items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
                    i = i + 1
            else:
                i = 1
                for anime in self.cached_list:
                    items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
                    i = i + 1
            walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(walker)
            self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
            self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
            self.view.set_focus('body')

            if self.listowner == self.username:
                self.display_to_top('MALSnakes - viewing your list   [' + self.list_sorts[self.list_sort_type] + ']')
            else:
                self.display_to_top('MALSnakes - viewing ' + self.listowner + "'s list   [" + self.list_sorts[self.list_sort_type] + ']')
        
        elif self.current_view == 2:
            self.anime_search_sort_type = (self.anime_search_sort_type + 1) % len(self.anime_search_sorts)
            if self.anime_search_sort_type == 0:
                malconstrict.helpers.sort_anime(self.cached_list, how='title')
            elif self.anime_search_sort_type == 1:
                malconstrict.helpers.sort_anime(self.cached_list, how='members_score', descending=True)
            items = []
            i = 1
            for anime in self.cached_list:
                items.append(ListItemWidget(i, anime.title + ' [' + str(anime.members_score) + ']', anime.id))
                i = i + 1
            walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(walker)
            self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
            self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
            self.view.set_focus('body')
            self.display_to_top('MALSnakes - showing results for "' + self.last_query + '"   [' + self.anime_search_sorts[self.anime_search_sort_type] + ']')


    def pull_in_list(self, username):
        """Pulls in a user's list."""
        self.display_to_top('MALSnakes - pulling in list...')
        self.current_view = 1
        lst = malconstrict.malapi.get_anime_list(username)
        if lst == None:
            lst = []
        else:
            lst = lst.anime
        self.listowner = username
        self.cached_list = lst
        categories = malconstrict.helpers.sort_anime_sectional(lst, how='title')
        self.cached_sections = categories
        self.catfocus = 0
        items = []
        i = 1
        cat_anime = categories[self.cats[self.catfocus]]
        items.append(CategoryItemWidget(self.cats[self.catfocus]))
        for anime in cat_anime:
            items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
            i = i + 1
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_focus('body')
        self.list_sort_type = 0
        
        if username == self.username:
            self.display_to_top('MALSnakes - viewing your list   [' + self.list_sorts[self.list_sort_type] + ']')
        else:
            self.display_to_top('MALSnakes - viewing ' + username + "'s list   [" + self.list_sorts[self.list_sort_type] + ']')


    def pull_in_anime_query_list(self, query):
        """Pulls in an anime's details"""
        self.current_view = 2
        self.display_to_top('MALSnakes - pulling in anime...')
        lst = malconstrict.malapi.search_anime(query)
        if lst == None:
            lst = []
        malconstrict.helpers.sort_anime(lst, how='title')
        self.cached_list = lst
        self.cached_sections = {}
        
        items = []
        i = 1
        for anime in lst:
            items.append(ListItemWidget(i, anime.title + ' [' + str(anime.members_score) + ']', anime.id))
            i = i + 1
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_focus('body')
        self.anime_search_sort_type = 0
        self.last_query = query
        self.display_to_top('MALSnakes - showing results for "' + self.last_query + '"   [' + self.anime_search_sorts[self.anime_search_sort_type] + ']')
        
        return
    
    
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
            self.foot, 'anime_entered', self.anime_entered)
        urwid.connect_signal(self.foot, 'query_escaped', self.query_escaped)
    

    def search_list(self):
        if self.current_view not in (1, 2):
            return
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
        self.display_to_top('MALSnakes - logged in as ' + self.username)
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
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'anime_entered', self.anime_entered)
        urwid.disconnect_signal(
            self, self.foot, 'query_escaped', self.query_escaped)
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.display_to_top('MALSnakes - showing results for "' + content + '"')
        self.pull_in_anime_query_list(content)
    
    
    def search_entered(self, content):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self, self.foot, 'search_entered', self.anime_entered)
        urwid.disconnect_signal(
            self, self.foot, 'query_escaped', self.query_escaped)
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        
        items = []
        # categories
        if self.current_view == 1 and self.list_sort_type in (0, 1):
            lst = malconstrict.helpers.search_substring(self.cached_sections[self.cats[self.catfocus]], content)
            i = 1
            items.append(CategoryItemWidget(self.cats[self.catfocus]))
            for anime in lst:
                items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
                i = i + 1
        # full
        elif (self.current_view == 1 and self.list_sort_type in (2, 3)) or self.current_view == 2:
            items = []
            lst = malconstrict.helpers.search_substring(self.cached_list, content)
            i = 1
            for anime in lst:
                if self.current_view == 1:
                    items.append(ListItemWidget(i, anime.title + ' [' + str(anime.score) + ']', anime.id))
                elif self.current_view == 2:
                    items.append(
                        ListItemWidget(i, anime.title + ' [' + str(anime.members_score) + ']', anime.id))
                i = i + 1
        
        walker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(walker)
        self.view.set_body(urwid.Frame(urwid.AttrWrap(self.listbox, 'body')))
        self.view.set_footer(urwid.AttrWrap(self.default_footer, 'foot'))
        self.view.set_focus('body')
    


if __name__ == '__main__':
    MyApp()