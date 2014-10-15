"""
CING: Common Interface for NMR structure Generation

Directories:

constants               CING constants, defenitions, parameters etc
core                    CING API basics
Database                Nomenclature database files
Legacy                  CING to maintain backward compatibility
Libs                    Library functionality including fast c code for cython.
nosetest                Directory with nose testing routines
PluginCode              Application specific code for e.g. validation programs.
Scripts                 Loose pieces of python CING code.
STAR                    Python API to STAR.


Files:

CONTENTS.txt            File with directory and file description.
localConstants.py       Settings that can be imported from python/cing/constants/definitions.py
                        NB this file is absent from svn. An example can be adapted
main.py                 The CING program.
setupCing.py            Run to set up environment variables and check installation.

"""

import time
import sys

#-----------------------------------------------------------------------------
# pydoc settings; also used by the program
#-----------------------------------------------------------------------------
__version__         =  '2.0.0'
__revision__        = '$Revision$'.split()[1]
__date__            = '$Date$'.split()[1]
__author__          = 'Geerten Vuister'
__copyright__       = 'Copyright (c) 2004-2014: Department of Biochemistry, University of Leicester, UK'
__copyright_years__ = '2004-' + time.asctime().split()[-1] # never have to update this again
__credits__         = 'More info at http://nmr.le.ac.uk'

#-----------------------------------------------------------------------------
# Cing Imports
#-----------------------------------------------------------------------------

from cing import constants

#-----------------------------------------------------------------------------
# Verbosity
#-----------------------------------------------------------------------------
# set verbosity to default
verbosity = constants.verbosity.default
###### legacy definitions Jurgen local override
try:
    from cing.localConstants import verbosity
except:
    pass
#end try

#-----------------------------------------------------------------------------
# System and cing definitions
#-----------------------------------------------------------------------------
from cing.constants.definitions import systemDefinitions
from cing.constants.definitions import cingDefinitions
from cing.constants.definitions import cingPaths
from cing.constants.definitions import directories

#-----------------------------------------------------------------------------
# create tmp directory
#-----------------------------------------------------------------------------
#
if cingDefinitions.tmpdir.exists():
    if cingDefinitions.tmpdir.isdir():
        cingDefinitions.tmpdir.rmdir()
    else:
        cingDefinitions.tmpdir.remove()
#end if
try:
    cingDefinitions.tmpdir.makedirs()
except:
    print("ERROR: Failed to create a temporary directory for %s at: %s" % (cingDefinitions.programName,cingDefinitions.tmpdir) )
    sys.exit(1)

#-----------------------------------------------------------------------------
###### legacy definitions
#-----------------------------------------------------------------------------
#starttime              = systemDefinitions.startTime
#osType                 = systemDefinitions.osType
verbosityNothing       = constants.verbosity.nothing # Even errors will be suppressed
verbosityError         = constants.verbosity.error   # show only errors
verbosityWarning       = constants.verbosity.warning # show errors and warnings
verbosityOutput        = constants.verbosity.output  # and regular output DEFAULT
verbosityDetail        = constants.verbosity.detail  # show more details
verbosityDebug         = constants.verbosity.debug   # add debugging info (not recommended for casual user)
verbosityDefault       = constants.verbosity.default

ncpus                  = constants.system.nCPU # use all if not specified by -c flag to main cing program.
internetConnected      = constants.system.internetConnected # Can be reset later when internet is up again

programName            = cingDefinitions.programName
cingVersion            = cingDefinitions.version
versionStr             = cingDefinitions.getVersionString()
cingRevision           = cingDefinitions.revision
cingRevisionUrl        = cingDefinitions.revisionUrl
issueListUrl           = cingDefinitions.issueUrl
authorList             = cingDefinitions.authors

# This code is repeated in __init__.py and setupCing.py please keep it sync-ed
cingPythonCingDir      = cingDefinitions.codePath  # os.path.split(__file__)[0]
# The path to add to your PYTHONPATH thru the settings script generated by cing.core.setupCing.py
cingPythonDir          = cingDefinitions.codePath[:-1]  # os.path.split(cingPythonCingDir)[0]
# Now a very important variable used through out the code. Even though the
# environment variable CINGROOT is defined the same this is the preferred
# source for the info within the CING python code.
cingRoot               = cingDefinitions.rootPath # os.path.split(cingPythonDir)[0]

cingDirTests           = cingRoot / "Tests"
cingDirMolmolScripts   = cingRoot / "scripts"  / "molmol"
cingDirTestsData       = cingRoot / "data" / "Tests"
cingDirScripts         = cingPythonCingDir / "Scripts"
cingDirLibs            = cingPythonCingDir / "Libs"
cingDirData            = cingRoot / "data"
cingDirTmp             = cingDefinitions.tmpdir

NaNstring              = constants.NaNstring

#-----------------------------------------------------------------------------
###### end legacy definitions
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Adaptations. TODO: cleanup
#-----------------------------------------------------------------------------
for key in cingPaths.keys():
    if cingPaths[ key ] == constants.PLEASE_ADD_EXECUTABLE_HERE:
        cingPaths[ key ] = None

if cingPaths.convert:
    cingPaths[ 'montage' ] = cingPaths.convert.replace('convert','montage')

# shiftx
if systemDefinitions.osType == constants.OS_TYPE_LINUX and systemDefinitions.osArchitecture == '64bit':
    cingPaths.shiftx = cingDefinitions.binPath / 'shiftx_linux64'
elif systemDefinitions.osType == constants.OS_TYPE_LINUX and systemDefinitions.osArchitecture == '32bit':
    cingPaths.shiftx = cingDefinitions.binPath / 'shiftx_linux'
elif systemDefinitions.osType == constants.OS_TYPE_MAC:
    cingPaths.shiftx = cingDefinitions.binPath / 'shiftx'
else:
    cingPaths.shiftx = None

# x3dna
if systemDefinitions.osType == constants.OS_TYPE_MAC:
    cingPaths.x3dna = cingDefinitions.binPath / 'x3dna'
else:
    cingPaths.x3dna = None

# molprobity
if systemDefinitions.osType == constants.OS_TYPE_MAC:
    cingPaths.MolProbity = cingDefinitions.binPath / 'molprobity'
else:
    cingPaths.MolProbity = None

if cingPaths.classpath:
    cingPaths.classpath = cingPaths.classpath.split(':')

#---------------------------------------------------------------------------------------------
# Define toplevel CING api
# dont move these to the top as they become circular.
# The order within this list is important too. For one thing, pydev extensions code analysis can't
# track imports well if not correct.
#---------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------
# functional imports: Order matters!
#---------------------------------------------------------------------------------------------

from cing.Libs import Adict

# Plugins
plugins = Adict.Adict() # Filled  later-on
from cing.core.importPlugin import importPlugins
importPlugins()                                  # This imports all plugins

# initialize the SMLhandler methods
__import__('cing.core.sml')

# database
from cing.core.database     import NTdb
NTdb._restoreFromSML()                          # This initializes the database

# json handlers
__import__('cing.core.jsonHandlers')
# xml handlers
__import__('cing.core.xmlHandlers')

#---------------------------------------------------------------------------------------------
# convenience
#---------------------------------------------------------------------------------------------
from cing.main import getInfoMessage as gi
from cing.Libs.io import formatDictItems as fd
from cing.core.importPlugin import importPlugin


