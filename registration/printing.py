#!/usr/bin/env python
#-*- coding:utf-8 -*-
# vim: set ts=4 sts=4

# For now the internal nametag templates will be hardcoded.  At least a [default]
# section is required; if a named section is missing the HTML will be ignored,
# otherwise the following sections and files are allowed:
#   - [parent]
#   - [report]
#   - [volunteer]

# TODO: respect locale's date/time format when doing substitution. Hard coded for now.
# TODO: abstract barcode generation in themes. Hard coded for now.
# TODO: a bunch of caching and restructuring.
# TODO: code for multiple copies, if needed.
# TODO: speed up batch printing with multi-page patched wkhtmltopdf?

"""Handles generation of HTML for nametags, saving/reading printer config, etc"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import re
import platform
import logging
import subprocess
import tempfile
import datetime
from configobj import ConfigObj

#from codebar import codebar
PRINT_MODE = 'pdf'

# Platforms using the CUPS printing system (UNIX):
unix = ['Linux', 'linux2', 'Darwin']
wkhtmltopdf = '/usr/local/bin/wkhtmltopdf' #path to wkhtmltopdf binary
#TODO: Option to select native or builtin wkhtmltopdf

#TODO: Determine whether to use ~/.taxidi/resources/ (config.ini in ~/.taxidi/)
#      or $PWD/resources/ (config.ini in pwd).
script_path = os.path.dirname(os.path.realpath(__file__))
nametags = os.path.join(script_path, 'resources', 'nametag') #path where html can be found.
#For distribution this may be moved to /usr/share/taxidi/ in UNIX, but should be
#copied to user's ~/.taxidi/ as write access is needed.
lpr = '/usr/bin/lpr' #path to LPR program (CUPS/Unix only).

class Printer:
    def __init__(self, local=False):
        self.log = logging.getLogger(__name__)
        if local:
            self.con = _DummyPrinter()
        else:
            if platform.system() in unix:
                self.log.info("System is type UNIX. Using CUPS.")
                self.con = _CUPS()
            elif platform.system() == 'win32':
                self.log.info("System is type WIN32. Using GDI.")
                #TODO implement win32 printing code
            else:
                self.log.warning("Unsupported platform. Printing by preview only.")

    def buildArguments(self, config, section='default'):
        """Returns list of arguments to pass to wkhtmltopdf. Requires config
        dictionary and section name to read (if None reads [default]).
        Works all in lowercase. If section name does not exist, will use
        values from [default] instead.
        """

        try: #attempt to read passed section. If invalid, use default instead.
            self.log.debug('Attempting to read print configuration for section {0}...'
                .format(section))
            piece = config[section]
        except KeyError:
            self.log.warn('No section for {0}: using default instead.'.format(section))
            piece = config['default']

        args = []
        if len(piece) == 0:
            return []  #No options in section
        for arg in piece.keys():
            if arg.lower() == 'zoom':
                args.append('--zoom')
                args.append(piece[arg])
            elif arg.lower() == 'size':
                args.append('-s')
                args.append(piece[arg])
            elif arg.lower() == 'height':
                args.append('--page-height')
                args.append(piece[arg])
            elif arg.lower() == 'width':
                args.append('--page-width')
                args.append(piece[arg])
            elif arg.lower() == 'left':
                args.append('--margin-left')
                args.append(piece[arg])
            elif arg.lower() == 'right':
                args.append('--margin-right')
                args.append(piece[arg])
            elif arg.lower() == 'top':
                args.append('--margin-top')
                args.append(piece[arg])
            elif arg.lower() == 'bottom':
                args.append('--margin-bottom')
                args.append(piece[arg])
            elif arg.lower() == 'orientation':
                args.append('--orientation')
                args.append(piece[arg].lower())
            else:
                self.log.warning("Unexpected key encountered in {0}: {1} = {2}"
                    .format(section, arg, piece[arg]))
        return args

    def writePdf(self, args, html, copies=1, collate=True):
        """
        Calls wkhtmltopdf and generates a pdf. Accepts args as a list, path
        to html file, and returns path to temporary file.  Temp file
        should be unlinked when no longer needed.
        Also accepts copies=1, collate=True
        """
        #Build arguments
        if copies < 0: copies = 1
        if copies != 1:
            args.append("--copies")
            args.append(copies)
        if collate:
            args.append("--collate")

        if type(html) == list:
          args += html
        else:
          args.append(html)

        #create temp file to write to
        out = tempfile.NamedTemporaryFile(delete=False)
        out.close()
        args.append(out.name) #append output file name

        self.log.debug('Calling {0} with arguments <'.format(wkhtmltopdf))
        self.log.debug('{0} >'.format(args))

        if args[0] != wkhtmltopdf: args.insert(0, wkhtmltopdf) #prepend program name

        ret = subprocess.check_call(args)
        if ret != 0:
            self.log.error('Called process error:')
            self.log.error('Program returned exit code {0}'.
                format(ret))
            return 0
        self.log.debug('Generated pdf {0}'.format(out.name))
        return out.name

    def preview(self, fileName):
        """Opens a file using the default application. (Print preview)"""
        if os.name == 'posix':
            if sys.platform == 'darwin': #OS X
                self.log.debug('Attempting to preview file {0} via open'
                    .format(fileName))
                ret = subprocess.call(['/usr/bin/open', fileName])
                if ret != 0:
                    self.log.error('open returned non-zero exit code {0}'.format(ret))
                    return 1
                return 0
            elif sys.platform == 'linux2': #linux
                try: #attempt to use evince-previewer instead
                    self.log.debug('Attempting to preview file {0} with evince.'
                        .format(fileName))
                    ret=subprocess.Popen(('/usr/bin/evince-previewer', fileName))
                    if ret != 0:
                        self.log.error('evince returned non-zero exit code {0}'
                            .format(ret))
                        return 1
                    return 0
                except OSError:
                    self.log.debug('evince unavailable.')

                self.log.debug('Attempting to preview file {0} via xdg-open'
                    .format(fileName))
                ret = subprocess.call(('/usr/bin/xdg-open', fileName))
                if ret != 0:
                    self.log.error('xdg-open returned non-zero exit code {0}'.format(ret))
                    return 1
                return 0
            else:
                self.log.warning('Unable to determine default viewer for POSIX platform {0}'.format(sys.platform))
                self.log.warning('Please file a bug and attach a copy of this log.')

        if os.name == 'nt': #UNTESTED
            self.log.debug('Attempting to preview file {0} via win32.startfile'
                .format(fileName))
            os.startfile(filepath)
            return 0

    def printout(self, filename, printer=None, orientation=None):
        if os.name == 'posix' or os.name == 'mac':  #use CUPS/lpr
            self.con.printout(filename, printer, orientation)

    #---- printing proxy methods -----

    def listPrinters(self):
        """Returns list of names of available system printers (proxy)."""
        return self.con.listPrinters()

    def getPrinters(self):
        """
        Returns dictionary of printer name, description, location, and URI (proxy)
        """
        return self.con.getPrinters()

class Nametag:
    def __init__(self, barcode=False):
        """
        Format nametags with data using available HTML templates.  Will
        fetch barcode encoding options from global config; otherwise accepts
        barcode=False as the initialization argument.
        """
        #TODO: source config options for barcode, etc. from global config.
        self.barcodeEnable = barcode
        self.log = logging.getLogger(__name__)

        #Setup and compile regex replacements:
        self.date_re = re.compile(r'%DATE%', re.IGNORECASE)       #date
        self.time_re = re.compile(r'%TIME%', re.IGNORECASE)       #time
        self.room_re = re.compile(r'%ROOM%', re.IGNORECASE)       #room
        self.first_re = re.compile(r'%FIRST%', re.IGNORECASE)     #name
        self.name_re = re.compile(r'%NAME%', re.IGNORECASE)     #name
        self.last_re = re.compile(r'%LAST%', re.IGNORECASE)       #surname
        self.medical_re = re.compile(r'%MEDICAL%', re.IGNORECASE) #medical
        self.code_re = re.compile(r'%CODE%', re.IGNORECASE)       #paging code
        self.secure_re = re.compile(r'%S%', re.IGNORECASE)        #security code
        self.title_re = re.compile(r'%TITLE%', re.IGNORECASE)        #security code
        self.number_re = re.compile(r'%NUMBER%', re.IGNORECASE)        #security code
        self.level_re = re.compile(r'%LEVEL%', re.IGNORECASE)        #security code
        self.age_re = re.compile(r'%AGE%', re.IGNORECASE)         #age

        self.medicalIcon_re = re.compile(
            r"window\.onload\s=\shide\('medical'\)\;", re.IGNORECASE)
        self.volunteerIcon_re = re.compile(
            r"window\.onload\s=\shide\('volunteer'\)\;", re.IGNORECASE)

    def listTemplates(self, directory=nametags):
        """Returns a list of the installed nametag themes"""
        #TODO: add more stringent validation against config and html.
        directory = os.path.abspath(directory)
        self.log.debug("Searching for html templates in {0}".format(directory))
        try:
            resource = os.listdir(directory)
        except OSError as e:
            logger.error('({0})'.format(e))
            return []

        themes = []
        #Remove any files from themes[] that are not directories:
        for i in resource:
            if os.path.isdir(os.path.join(directory, i)):
                themes.append(i)

        valid = []
        #Check that each folder has the corresponding .conf file:
        for i in themes:
            if os.path.isfile(self._getTemplateFile(i)):
                valid.append(i)

        valid.sort()
        del resource, themes
        self.log.debug("Found templates {0}".format(valid))
        return valid

    def _getTemplateFile(self, theme, directory=nametags):
        """
        Returns full path to .conf file for an installed template pack and
        check it exists.
        """
        directory = os.path.abspath(directory)
        path = os.path.join(directory, theme, '{0}.conf'.format(theme))
        #TODO: more stringent checks (is there a matching HTML file?)
        if os.path.isfile(path):
            return path
        else:
            self.log.warning("{0} does not exist or is not file.".format(path))

    def _getTemplatePath(self, theme, directory=nametags):
        """Returns absolute path only of template pack"""
        return os.path.join(directory, theme)


    def readConfig(self, theme):
        """
        Reads the configuration for a specified template pack. Returns
        dictionary.
        """
        inifile = self._getTemplateFile(theme)
        self.log.info("Reading template configuration from '{0}'"
            .format(inifile))
        config = ConfigObj(inifile)
        try: #check for default section
            default = config['default']
        except KeyError as e:
            self.log.error(e)
            self.log.error("{0} contains no [default] section and is invalid."
                .format(inifile))
            raise KeyError("{0} contains no [default] section and is invalid."
                .format(inifile))
        del default
        return config

    def nametag(self, template='apis', name='', number='', title='', level='', age='', barcode=False):
    #def nametag(self, template='default', room='', first='', last='', medical='',
    #            code='', secure='', barcode=True):

        #Check that theme specified is valid:
        if template != 'default':
            themes = self.listTemplates()
            if template not in themes:
                self.log.error("Bad theme specified.  Using default instead.")
                template = 'default'
        #Read in the HTML from template.
        try:
            directory = self._getTemplatePath(template)
        except KeyError:
            self.log.error("Unable to process template '{0}'. Aborting."
                .format(template))
            return None

        #read in the HTML
        self.log.debug('Generating nametag with nametag()')
        self.log.debug('Reading {0}...'.format(os.path.join(directory,
            'default.html')))
        f = open(os.path.join(directory, 'default.html'))
        html = f.read()
        f.close()

        if len(html) == 0: #template file is empty: use default instead.
            self.log.warn('HTML template file {0} is blank.'.format(
                          os.path.join(directory, 'default.html')))

        #generate barcode of secure code, code128:
        if barcode:
            try:
                if secure == '':
                    codebar.gen('code128', os.path.join(directory,
                        'default-secure.png'), code)
                else:
                    codebar.gen('code128', os.path.join(directory,
                        'default-secure.png'), secure)
            except NotImplementedError as e:
                self.log.error('Unable to generate barcode: {0}'.format(e))
                html = html.replace('default-secure.png', 'white.gif')
        else:
            #replace barcode image with white.gif
            html = html.decode('utf-8').replace('default-secure.png', 'white.gif')
            self.log.debug("Disabled barcode.")

        #get the current date/time
        now = datetime.datetime.now()

        #Perform substitutions:
        html = self.date_re.sub(now.strftime("%a %d %b, %Y"), html)
        html = self.time_re.sub(now.strftime("%H:%M:%S"), html)
        #Fix for if database returns None instead of empty string:
        html = self.name_re.sub(name.encode('utf-8'), html.encode('utf-8'))
        html = self.level_re.sub(str(level), html)
        html = self.title_re.sub(str(title), html)
        html = self.number_re.sub(str(number), html)
        html = self.age_re.sub(str(age), html)

        return html

class _DummyPrinter:
    def __init__(self):
        self.con = None
    def listPrinters(self):
        return []
    def getPrinters(self):
        return {}
    def returnDefault(self):
        return ''
    def printout(self, filename, printer=None, orientation=None):
        raise PrinterError('No printer system available')

class _CUPS:
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.info("Connecting to CUPS server on localhost...")
        try:
            import cups
        except ImportError as e:
            self.log.error("CUPS module not available.  Is CUPS installed? {0}".format(e))
        self.con = cups.Connection()

    def listPrinters(self):
        """
        Returns a list of the names of available system printers.
        """
        return list(self.con.getPrinters().keys())

    def getPrinters(self):
        """
        Returns dictionary of printer name, description, location, and URI.
        """
        a = dict()
        printers = self.con.getPrinters()
        for item in printers:
            info = printers[item]['printer-info']
            location = printers[item]['printer-location']
            uri = printers[item]['device-uri']
            a[item] = { 'info' : info, 'location' : location, 'uri' : uri}
        return a

    def getDefault(self):
        """Determines the user's default system or personal printer."""
        return self.con.getDests()[None, None].name

    def printout(self, filename, printer=None, orientation=None):
        if printer != None: #set printer; if none, then use default (leave argument blank)
            if printer not in self.listPrinters():
                raise PrinterError('Specified printer is not available on this system')
            printArgs = ['-P', printer]
        else:
            printArgs = []

        if orientation: #set orientation option
            if orientation not in ['landscape', 'portrait']:
                raise PrinterError('Bad orientation specification: {0}'.format(orientation))
            printArgs.append('-o')
            printArgs.append(orientation)

        try: #see if file exists
            f = open(filename)
        except IOError:
            raise PrinterError('The specified file does not exist: {0}'.format(filename))
        else:
            f.close()
        printArgs.append(filename) #append file to print.

        ret = subprocess.check_call([lpr,] + printArgs)
        if ret != 0:
            raise PrinterError('{0} exited non-zero ({1}).  Error spooling.'.format(lpr, ret))


class PrinterError(Exception):
    def __init__(self, value=''):
        if value == '':
            self.error = 'Generic spooling error.'
        else:
            self.error = value
    def __str__(self):
        return repr(self.error)


class Main:
    def __init__(self, local=False):
        self.log = logging.getLogger(__name__)
        self.con = Printer(True)
        self.tag = Nametag(True)
        self.section = ''

    def nametag(self, theme='apis', name='', number='', title='', level='', barcode=False, section='default'):
    #def nametag(self, theme='default', room='', first='', last='', medical='',
    #            code='', secure='', barcode=True, section='default'):
        """Note: section= not fully implemented in Nametag.nametag method"""
        self.section = section
        self.conf = self.tag.readConfig(theme) #theme
        self.args = self.con.buildArguments(self.conf, section) #section

        stuff = self.tag.nametag(name=name, number=number, title=title, template=theme, level=level)
        temp_path = self.tag._getTemplatePath(theme)
        html = tempfile.NamedTemporaryFile(delete=False, dir=temp_path, suffix='.html')
        html.write(stuff.encode('utf-8'))
        html.close()

        self.pdf = self.con.writePdf(self.args, html.name)
        os.unlink(html.name)
        return self.pdf

    def nametags(self, tags, theme='apis', section='default'):
        self.section = section
        self.conf = self.tag.readConfig(theme) #theme
        self.args = self.con.buildArguments(self.conf, section) #section

        html_files = []
        for data in tags:
            stuff = self.tag.nametag(
                    name=data['name'], number=data['number'],
                    title=data['title'], template=theme, level=data['level'],
                    age=data['age']
            )
            temp_path = self.tag._getTemplatePath(theme)
            html = tempfile.NamedTemporaryFile(delete=False, dir=temp_path, suffix='.html')
            html.write(stuff)
            html.close()
            html_files.append(html.name)

        self.pdf = self.con.writePdf(self.args, html_files)
        for tmpname in html_files:
            #os.unlink(tmpname)
            pass
        return self.pdf


    def preview(self, filename=None):
        if filename == None:
            filename = self.pdf
        self.con.preview(filename)

    def printout(self, filename=None, printer=None, orientation=None):
        if filename == None:
            filename = self.pdf
        if orientation == None:
            orientation = self.conf[self.section]['orientation']
        self.con.printout(filename, printer, orientation)

    def cleanup(self, trash=None):
        if trash != None:
            for item in trash:
                os.unlink(item)
        else:
            os.unlink(self.pdf)
        self.section = ''

if __name__ == '__main__':

    tags =  [
            { 'name' : "Barkley Woofington", 'number' : "S-6969", 'level' : "Top Dog", 'title' : '' , 'age' : 20},
            { 'name' : "Rechner Foxer", 'number' : "S-0001", 'level' : "Foxo", 'title' : '' , 'age' : 12}
    ]

    con = Main(False)
    con.nametags(tags, theme='apis')
    #con.nametag(theme='apis', name="Some Kind Of Horse", number="S-0000", title="Staff", level="Player")

    print(con.pdf)
    con.preview()
    #con.printout(printer="LabelWriter-450-Turbo")

    if sys.version_info[0] == 2:
        raw_input(">")
    else:
        input(">")
    con.cleanup()
