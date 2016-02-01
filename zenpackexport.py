#! /usr/bin/env python

import string
import sys
import Globals
import StringIO
import os
import subprocess
from argparse import ArgumentParser

from Products.ZenUtils.Utils import zenPath 
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from transaction import commit


def eliminateDuplicates(objs):
    """
    Given a list of objects, return the sorted list of unique objects
    where uniqueness is based on the getPrimaryPath() results.

    @param objs: list of objects
    @type objs: list of objects
    @return: sorted list of objects
    @rtype: list of objects
    """

    objs.sort(key = lambda x: x.getPrimaryPath())
    result = []
    for obj in objs:
        for alreadyInList in result:
            path = alreadyInList.getPrimaryPath()
            if obj.getPrimaryPath()[:len(path)] == path:
                break
        else:
            result.append(obj)
    return result

def main():

    parser = ArgumentParser(description='Export Zenpacks from the cli')
    parser.add_argument ('-z', '--zenpack', action='store', dest='packname', required=True, help='ZenPack name to export')
    parser.add_argument ('-b', '--build', action='store_true', dest='build', default=False, help='Build and export an egg')
    parser.add_argument ('-p', '--path', action='store', dest='exportpath', default='default', help='Path to export egg to')

    results = parser.parse_args()

    dmd = ZenScriptBase(connect=True, noopts=True).dmd
    for pack in dmd.ZenPackManager.packs():
        if pack.id == results.packname:
    
            if not pack.isDevelopment():
                print "Zenpack not in development mode, so can't be exported"
                sys.exit(1)

            xml = StringIO.StringIO()

            xml.write("""<?xml version="1.0"?>\n""")
            xml.write("<objects>\n")
            packables = eliminateDuplicates(pack.packables())
            for obj in packables:
                xml.write('<!-- %r -->\n' % (obj.getPrimaryPath(),))
                obj.exportXml(xml,['devices','networks','pack'],True)
            xml.write("</objects>\n")
            path = pack.path('objects')
            if not os.path.isdir(path):
                os.mkdir(path, 0750)
            objects = file(os.path.join(path, 'objects.xml'), 'w')
            objects.write(xml.getvalue())
            objects.close()

            print "Created objects.xml"

            path = pack.path('skins')
            if not os.path.isdir(path):
                os.makedirs(path, 0750)

            init = pack.path('__init__.py')
            if not os.path.isfile(init):
               fp = file(init, 'w')
               fp.write(
'''
import Globals
from Products.CMFCore.DirectoryView import registerDirectory
registerDirectory("skins", globals())
''')
               fp.close()
            print "created skins folder"

            if results.build == True:
 
                if results.exportpath == 'default':
                    exportDir = zenPath('export')
                else:
                    exportDir = results.exportpath
  
                if not os.path.isdir(exportDir):
                    os.makedirs(exportDir, 0750)
                
                eggPath = pack.eggPath()
                os.chdir(eggPath)
 
                if os.path.isdir(os.path.join(eggPath, 'dist')):
                    os.system('rm -rf dist/*') 

                p = subprocess.Popen('python setup.py bdist_egg', stderr=sys.stderr, shell=True, cwd=eggPath)
                p.wait()
                os.system('cp dist/* %s' % exportDir)
                print "Exported " + pack.eggName()

if __name__ == '__main__':
    main()



