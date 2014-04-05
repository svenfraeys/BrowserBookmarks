import json, os, subprocess
import sublime_plugin, sublime
import urllib.parse as urlparse
import webbrowser
import os

VERBOSE = 6
def log(message,verbose=1):
    '''print a message with verbose limit
    '''
    if verbose <= VERBOSE:
        print('%s:%s' % (verbose, message) )

def browse_to(url):
    '''go to specific url
    '''
    webbrowser.open_new_tab(url)
    # subprocess.Popen(['iceweasel','-new-tab',url])

class Bookmark(object):
    def __init__(self, dataDict=None):
        self._dataDict = dataDict
        self._name    = None
        self._type     = None
        self._url      = None
        self._parent   = None
        self._children = []

    def parent(self):
        '''get parent
        '''
        return self._parent
    
    def setParent(self, value):
        '''set parent
        '''
        self._parent = value
    
    def dataDict(self):
        ''' get self._dataDict
        '''
        return self._dataDict
    
    def setDataDict(self, value):
        ''' set self._dataDict
        '''
        self._dataDict = value
    
    def type(self):
        ''' get self._type
        '''
        return self._type
    
    def setType(self, value):
        ''' set self._type
        '''
        self._type = value
    
    def url(self):
        ''' get self._url
        '''
        return self._url
    
    def setUrl(self, value):
        ''' set self._url
        '''
        self._url = value
    
    def name(self):
        '''get name
        '''
        return self._name
    
    def setName(self, value):
        '''set name
        '''
        self._name = value
    
    def grandParents(self):
        '''return all grandParents
        '''
        grandParents = []
        parent = self.parent()
        if parent:
            grandParents.append(parent)
            grandParents += parent.grandParents()

        return grandParents

    def grandChildren(self):
        grandChildren = []
        childs = self.children()

        for child in childs:
            grandChildren.append(child)
            subchilds = child.grandChildren()
            grandChildren += subchilds

        return grandChildren
        
    def children(self):
        '''get children
        '''
        return self._children
    
    def setChildren(self, value):
        '''set children
        '''
        self._children = value
    
class BookmarkFirefox(object):
    def __init__(self, dataDict):
        self._dataDict = dataDict

    def dataDict(self):
        '''get dataDict
        '''
        return self._dataDict
    
    def setDataDict(self, value):
        '''set dataDict
        '''
        self._dataDict = value

    def type(self):
        dataDict = self.dataDict()
        return dataDict['type']

    def title(self):
        dataDict = self.dataDict()
        return dataDict['title']  

    def uri(self):
        dataDict = self.dataDict()
        if 'uri' not in dataDict:
            return None

        return dataDict['uri']        

    def grandChildren(self):
        grandChildren = []
        childs = self.children()

        for child in childs:
            grandChildren.append(child)
            subchilds = child.grandChildren()
            grandChildren += subchilds

        return grandChildren

    def children(self):
        dataDict = self.dataDict()
        if 'children' not in dataDict:
            return []

        childs = dataDict['children']
        children = []
        for child in childs:
            children.append(BookMark(child))

        return children

class BookmarkChrome(Bookmark):
    def __init__(self, dataDict):
        super(BookmarkChrome, self).__init__(dataDict)
        self._dataDict = dataDict

    def dataDict(self):
        '''get dataDict
        '''
        return self._dataDict
    
    def setDataDict(self, value):
        '''set dataDict
        '''
        self._dataDict = value

    def type(self):
        dataDict = self.dataDict()
        return dataDict['type']

    def name(self):
        dataDict = self.dataDict()
        return dataDict['name']  

    def url(self):
        dataDict = self.dataDict()
        if 'url' not in dataDict:
            return None

        return dataDict['url']        

    def children(self):
        dataDict = self.dataDict()
        if 'children' not in dataDict:
            return []

        childs = dataDict['children']
        children = []
        for child in childs:
            childBookmark = BookmarkChrome(child)
            childBookmark.setParent(self)
            children.append(childBookmark)

        return children



class BookmarksFirefox(object):
    def get_bookmark_urls():
        root = '/home/sven.fr/.mozilla/firefox/5ssz988r.default/bookmarkbackups'
        jsonFileNames = os.listdir(root)
        jsonFileNames.sort()
        filePath = os.path.join( root, jsonFileNames[-1])
        log(filePath)
        
        # filePath = '/home/sven.fr/.mozilla/firefox/5ssz988r.default/bookmarkbackups/bookmarks-2014-03-21.json'
        fs = open(filePath,'r')
        rootBookmark = json.load(fs)
        fs.close()

        # bookmarks = json.dumps(rootBookmark, sort_keys=True ,ensure_ascii=True ,indent=4)
        # print(bookmarks)
        bm = BookMark(rootBookmark)
        childs = bm.grandChildren()
        log('childs=%s' % len(childs), 6)

        returnList = []

        for child in childs:
            url = child.url()
            if url:
                if url.find('place') != -1:
                    continue

            title = child.title()
            if not title or title == '':
                parsed_url = urlparse.urlparse( url )
                domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
                domain = domain.replace('http://','')
                domain = domain.replace('https://','')
                domain = domain.replace('/','')
                log(domain)
                title = domain

            if uri:
                returnList.append( [title, uri] )
            

        return returnList

class BookmarksChrome():
    def bookmarks(self):
        localAppData = os.getenv('LOCALAPPDATA')
        bookmarks = os.path.join(localAppData, 'Google', 'Chrome', 'User Data', 'Default', 'bookmarks')

        # bookmarks = r'C:\Users\sven\AppData\Local\Google\Chrome\User Data\Default\bookmarks'
        fs = open(bookmarks, 'r')
        dataDict = json.load(fs)
        fs.close()

        bookmarks = []
        for root in dataDict['roots']:
            rootDict = dataDict['roots'][root]
            log('type(root)=%s' % type(root), 6)
            if type(rootDict) != dict:
                continue

            bookmark = BookmarkChrome(rootDict)

            bookmarks.append(bookmark)

            bookmarks += bookmark.grandChildren()

        return bookmarks

class ShowBookmarksCommand(sublime_plugin.WindowCommand):
    def settings(self):
        '''return if the fold getters and setters is active or not
        '''
        settings = sublime.load_settings("BrowserBookmarks.sublime-settings")
        return settings

    def collectBookmarks(self):
        returnBookmarks = []
        if self.settings().get("chrome") is True:
            chrome = BookmarksChrome()
            for bookmark in chrome.bookmarks():
                if bookmark.type() != 'folder':
                    returnBookmarks.append(bookmark)

        return returnBookmarks

    def handleHelpSelect(self, index):
        '''open the current project
        '''
        log('index=%s' % index, 6)

        if index == -1:
            return
        
        bookmarks = self.collectBookmarks()
        bookmark = bookmarks[index]
        uri = bookmark.url()
        browse_to( uri )

    def run(self):
        log('help',1)
        
        quickPanelData = []
        bookmarks = self.collectBookmarks()
        log('bookmarks=%s' % bookmarks, 6)


        for bookmark in bookmarks:
            
            title = bookmark.name()
            url = bookmark.url()
            title = bookmark.name()
            subTitle = bookmark.url()

            parsed_url = urlparse.urlparse( url )
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)

            # construct nez title if empty
            if not title or title == '':
                parsed_url = urlparse.urlparse( url )
                domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
                domain = domain.replace('http://','')
                domain = domain.replace('https://','')
                domain = domain.replace('/','')
                log(domain)
                title = domain

            parents = bookmark.grandParents()

            hierarchy = None
            if len(parents) > 0:
                parents.reverse()

                hierarchy = '>'.join ( [parent.name() for parent in parents] )

            displayList = [title]


            if hierarchy:
                displayList.append('%s' % (hierarchy) )

            log('hierarchy=%s' % hierarchy, 6)
            quickPanelData.append ( displayList )

        log('quickPanelData=%s' % quickPanelData, 6)

        sublime.active_window().show_quick_panel(quickPanelData, self.handleHelpSelect)

        return
        bookmarks = get_bookmark_urls()
        log(bookmarks,1)
        label = [bookmark for bookmark in bookmarks]
        log(label,1)
        sublime.active_window().show_quick_panel(bookmarks, self.handleHelpSelect)

# get_bookmark_urls()


# chrome = BookmarksChrome()
# for bookmark in chrome.bookmarks():
#     print(bookmark.grandParents())