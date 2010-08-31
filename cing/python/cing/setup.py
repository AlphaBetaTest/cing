# Please note the lack of imports here to cing specific code.
# The idea is that this script runs without PYTHONPATH being set yet.
from string import atoi
from string import strip
from subprocess import PIPE
from subprocess import Popen
import os
import sys
import time
#from cing.Libs.disk import chmod #AWSS, importing cing stuff here is not fine.

"""
python YOUR_CING_PATH_HERE/python/cing/setup.py
E.g.:
python /Users/jd/workspace/cing/python/cing/setup.py

Generates either cing.csh or cing .sh to source in your .cshrc or .bashrc
(or equivalent) respective file

Adjust if needed.

GV:  16 Sep 2007: added cingBinPath and profitPath
JFD: 27 Nov 2007: removed again.
GV:  13 Jun 2008: Added CYTHON path and refine, cyana2cing and cython aliases
JFD: 26 May 2009: Added pyMol path

Uses 'which xplor/$prodir/procheck_nmr.scr/DO_WHATIF.COM' to determine initial
xplor/procheck/what if executables; make sure they are in your
path when you run setup. If they are not; you may continue without their
respective functionalities.
"""

#Block to keep in sync with the one in helper.py
#===============================================================================
def _NTgetoutput( cmd ):
    """Return output from command as (stdout,sterr) tuple"""
#    inp,out,err = os.popen3( cmd )
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    (inp,out,err) = (p.stdin, p.stdout, p.stderr)

    output = ''
    for line in out.readlines():
        output += line
    errors = ''
    for line in err.readlines():
        errors += line
    inp.close()
    out.close()
    err.close()
    return (output,errors)
def _NTerror(msg):
    print "ERROR:",msg
def _NTwarning(msg):
    print "WARNING:",msg
def _NTmessage(msg):
    print msg
#===============================================================================

#------------------------------------------------------------------------------------
# generate setup csh or bash script
#------------------------------------------------------------------------------------

PLEASE_ADD_EXECUTABLE_HERE = "PLEASE_ADD_EXECUTABLE_HERE"

CING_SHELL_TEMPLATE = \
'''
#############################################
# adjust these, if needed
#############################################
%(export)s  xplorPath%(equals)s%(xplorPath)s
%(export)s  procheckPath%(equals)s%(procheckPath)s
%(export)s  aqpcPath%(equals)s%(aqpcPath)s
%(export)s  whatifPath%(equals)s%(whatifPath)s
%(export)s  dsspPath%(equals)s%(dsspPath)s
%(export)s  convertPath%(equals)s%(convertPath)s
%(export)s  ghostscriptPath%(equals)s%(ghostscriptPath)s
%(export)s  ps2pdfPath%(equals)s%(ps2pdfPath)s
%(export)s  molmolPath%(equals)s%(molmolPath)s
%(export)s  povrayPath%(equals)s%(povrayPath)s
%(export)s  talosPath%(equals)s%(talosPath)s
#############################################
# No changes needed below this line.
#############################################
%(export)s  CINGROOT%(equals)s%(cingRoot)s
%(export)s  CYTHON%(equals)s%(cingRoot)s/dist/Cython
%(export)s  PYMOL_PATH%(equals)s%(pyMolPath)s
%(export)s  YASARA_PATH%(equals)s%(yasaraPath)s

# Adding each component individually to PYTHONPATH
%(export)s  CING_VARS%(equals)s$CINGROOT/python
%(export)s  CING_VARS%(equals)s${CING_VARS}:$CYTHON
%(export)s  CING_VARS%(equals)s${CING_VARS}:$PYMOL_PATH/modules
%(export)s  CING_VARS%(equals)s${CING_VARS}:$YASARA_PATH/yasara/pym:$YASARA_PATH/yasara/plg

if %(conditional)s then
    %(export)s PYTHONPATH%(equals)s${CING_VARS}:${PYTHONPATH}
else
    %(export)s PYTHONPATH%(equals)s${CING_VARS}
%(close_if)s

# Use -u to ensure messaging streams for stdout/stderr don't mingle (too much).
alias cing%(equals)s'python -u $CINGROOT/python/cing/main.py'
alias cyana2cing%(equals)s'python -u $CINGROOT/python/cyana2cing/cyana2cing.py'
alias refine%(equals)s'python -u $CINGROOT/python/Refine/refine.py'
alias cython%(equals)s'$CYTHON/bin/cython'

'''
# make the addition conditional to presence like for tcsh.
#if ( $PYMOL_PATH != 'PLEASE_ADD_EXECUTABLE_HERE' ) then
#    setenv  CING_VARS ${CING_VARS}:$PYMOL_PATH/modules
#endif

#------------------------------------------------------------------------------------

######################################################################################################
# This code is repeated in __init__.py and setup.py please keep it sync-ed
cingPythonCingDir = os.path.split(os.path.abspath(__file__))[0]
# The path to add to your PYTHONPATH thru the settings script generated by cing.core.setup.py
cingPythonDir = os.path.split(cingPythonCingDir)[0]
# Now a very important variable used through out the code. Even though the
# environment variable CINGROOT is defined the same this is the preferred
# source for the info within the CING python code.
cingRoot = os.path.split(cingPythonDir)[0]
#NTdebug("cingRoot        : " + cingRoot)
######################################################################################################

######################################################################################################
# This code is repeated in cing/setup.py and cing/Libs/NTutils.py please keep it sync-ed
######################################################################################################

def check_python():
    hasDep = True
    version = float(sys.version[:3])
    if version < 2.5:
        _NTerror('Failed to find Python version 2.5 or higher.')
        _NTerror('Current version is %s' % sys.version[:5])
        _NTerror("Python 2.4 in the package managers such as yum, fink, port, and apt come with a 'mat plot lib' version that doesn't work with CING.")
        hasDep = False
    if hasDep:
        _NTmessage("........ Found 'Python'")
    else:
        _NTwarning('Failed to find good python.')

def check_matplotlib():
    hasDep = True
    try:
        from matplotlib.axis import XAxis
    except:
        hasDep = False
        _NTerror('Failed to find matplotlib. Absolutely required for CING')

    if hasDep:
        try:
            from matplotlib.pylab import axes
            xaxis = XAxis(axes([.1, .1, .8, .8 ]))
            if not hasattr(xaxis, 'convert_units'):
                hasDep = False
                _NTerror('Failed to find good matplotlib. Absolutely required for CING. Look for version 0.98.3-1 or higher. Developed with 0.98.5-1')
        except:
            hasDep = False

    if hasDep:
        _NTmessage("........ Found 'matplotlib'")



def check_pylab():
#    print 'Matplotlib module  ',
    result = 0
    try:
        import matplotlib.pylab #@UnusedImport
#        print 'ok.'
        result = 1
    except:
        _NTwarning('Failed to find Matplotlib.')
    if result:
        _NTmessage("........ Found 'Matplotlib.pylab'")
    return result

def check_ccpn():
#    print '\nCCPN distribution:',

    missing = []
    gotRequiredCcpnModules = False
    try:
        import ccpnmr #@UnusedImport @UnresolvedImport
        gotRequiredCcpnModules = True
#        print 'ok.'
    except:
        missing.append('ccpnmr')
#        print

    # JFD disabled these since they aren't used in CING (?yet).
#    try:
#        import ccpnmr.format #@UnusedImport @Reimport
#        _NTmessage("Found 'FormatConverter'")
#    except:
#        missing.append('ccpnmr.format')
#
#    try:
#        import ccpnmr.analysis #@UnusedImport @Reimport @UnresolvedImport
#        print 'Anaysis: ok.'
#    except:
#        missing.append('ccpnmr.analysis')

    if gotRequiredCcpnModules:
        _NTmessage("........ Found 'CCPN'")
    else:
        _NTmessage("Could not find 'CCPN' (optional)")

#    if missing:
#        _NTmessage( 'Missing (optional) packages: ' + ', '.join(missing))

# disabled for this needs to be no extra- dependency. A version of numarray should
# be in matplotlib. In fact the code doesn't refer to numarray anywhere. Or JFD
# can't find it. Did Alan meant to check for things like: from matplotlib.numerix import nan # is in python 2.6 ?
#def check_numarray():
#
#    print 'Numarray module   ',
#    result = 0
#    try:
#        import numarray #@UnusedImport
#        print 'ok.'
#        result = 1
#    except:
#        print 'could not import Numarray module.'
#
#    return result

# See above.
#def check_numpy():
#
#    print 'Numpy module   ',
#    result = 0
#    try:
#        import numpy #@UnusedImport
#        print 'ok.'
#        result = 1
#    except:
#        print 'could not import Numpy module.'
#
#    return result

def check_cython():

#    print 'Cython module   ',
    result = 0
    try:
        import Cython.Distutils #@UnusedImport @UnresolvedImport
#        print 'ok.'
        result = 1
#        print "Great you have Cython! Please try to compile CING's Cython libs running:"
#        print 'cd %s/python/cing/Libs/cython; python compile.py build_ext --inplace; cd -' % cingRoot

        # JFD disabled this until we get it to work on our Macs.
#        os.chdir(os.path.join(cingRoot,'python/cing/Libs/cython'))
#        out = call(['python', 'compile.py','build_ext', '--inplace'])
#        if out:
#            print '==> Failed to compile CING Cython libs.'
#            print '    Good chance it will run by hand, try running:\n%s' % cmd
#            print '    If your using Mac, see "https://bugs.launchpad.net/cython/+bug/179097"'
    except:
#        print 'failed to import Cython module.'
        pass

    if not result:
        _NTwarning('Failed to find Cython')
    else:
        _NTmessage("........ Found 'Cython'")

    return result

# JFD This one is even disabled in the test since some time now.
#def check_profiler():
#
#    print 'Profiler module   ',
#    result = 0
#    try:
#        import profile #@UnusedImport
#        print 'ok.'
#        result = 1
#    except:
#        print 'could not import Profiler module.'
#        print "it's not essencial but used with 'cing --test'."
#    return result


def _writeCingShellFile(isTcsh):
    '''Generate the Cing Shell file for csh or bash'''
    if isTcsh:
        parametersDict['export'] = 'setenv'
        parametersDict['equals'] = ' '
        parametersDict['conditional'] = '($?PYTHONPATH)'
        parametersDict['close_if'] = 'endif'
        parametersDict['equals'] = ' '
        sourceCommand = 'source'
        cname = 'cing.csh'
    else:
        parametersDict['export'] = 'export'
        parametersDict['equals'] = '='
        parametersDict['conditional'] = '[ ! -z "${PYTHONPATH}" ];'
        parametersDict['close_if'] = 'fi'
        sourceCommand = '.'
        cname = 'cing.sh'
#    NTdebug("pars:" + `parametersDict`)
    text = CING_SHELL_TEMPLATE % parametersDict
    if isTcsh:
        text += "\nrehash\n"
    cname = os.path.join( cingRoot, cname )
    fp = open(cname,'w')
    fp.write(text)
    fp.close()

    print ''
    print '==> Please check/modify %s <===' % (cname)
    print '    Then activate it by sourcing it in your shell settings file (.cshrc or .bashrc):'
    print ''
    print '    %s %s' % ( sourceCommand, cname)
    print ''
    print ''
    print '==> Note by JFD'
    print ' There is another dependency; cython. Please install it and run:'
    print ' cd $CINGROOT/python/cing/Libs/cython; python compile.py build_ext --inplace'
    print ' After installing cython; rerun setup.py or manually update the settings file.'
    print ' We have included the Cython distribution needed so add to your PYTHONPATH for now:'
    print ' $CINGROOT/dist/Cython (later it will be added by the cing.[c]sh created.'
    
#end def
#------------------------------------------------------------------------------------


if __name__ == '__main__':
#    cing.verbosity = verbosityOutput # Default is no output of anything.

    check_python()
    check_matplotlib()
    check_ccpn()
    check_pylab()
#    check_numpy()
#    check_numarray()
    check_cython()

    if not cingRoot:
        print "Failed to derive the CINGROOT from this setup.py script; are there other setup.py or code confusing me here?"
        sys.exit(1)

    if not os.path.exists(cingRoot):
        print "The derived CINGROOT does not exist: ["  + cingRoot + "]"
        sys.exit(1)

    if not cingPythonDir:
        print "Failed to derive the CING python directory from this setup.py script. No clue why?"
        sys.exit(1)

    parametersDict = {}
    parametersDict['cingPythonDir'] = cingPythonDir
    parametersDict['cingRoot']      = cingRoot

    xplorPath,err  = _NTgetoutput('which xplor')
    if not xplorPath:
        _NTmessage("Could not find 'xplor'")
        parametersDict['xplorPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'xplor'")
        parametersDict['xplorPath']  = strip(xplorPath)

#    procheckPath,err  = _NTgetoutput('which $prodir/procheck_nmr.scr')
    if os.environ.has_key("prodir"):
        procheckPath = os.path.join( os.environ["prodir"], "procheck_nmr.scr")
        if not os.path.exists(procheckPath):
            _NTwarning("Found the system variable prodir but the script below was not found")
            _NTwarning( procheckPath )
            _NTwarning("Could not find 'procheck_nmr'")
            parametersDict['procheckPath']  = PLEASE_ADD_EXECUTABLE_HERE
        else:
            _NTmessage("........ Found 'procheck_nmr'")
            parametersDict['procheckPath'] = procheckPath
    else:
        _NTmessage("Could not find 'procheck_nmr'")
        parametersDict['procheckPath']  = PLEASE_ADD_EXECUTABLE_HERE

#    procheckPath,err  = _NTgetoutput('which $prodir/procheck_nmr.scr')
    if os.environ.has_key("aquaroot"):
        aqpcPath = os.path.join( os.environ["aquaroot"], "scripts", "aqpc")
        if not os.path.exists(aqpcPath):
            _NTwarning("Found the system variable aquaroot but the script below wasn't found")
            _NTwarning( aqpcPath )
            _NTwarning("Could not find 'aqua'")
            parametersDict['aqpcPath']  = PLEASE_ADD_EXECUTABLE_HERE
        else:
            _NTmessage("........ Found 'aqua'")
            parametersDict['aqpcPath'] = aqpcPath
    else:
        _NTmessage("Could not find 'aqua'")
        parametersDict['aqpcPath']  = PLEASE_ADD_EXECUTABLE_HERE

    whatifPath,err  = _NTgetoutput('which DO_WHATIF.COM')
    parametersDict['whatifPath']  = PLEASE_ADD_EXECUTABLE_HERE
    parametersDict['dsspPath']    = PLEASE_ADD_EXECUTABLE_HERE
    if not whatifPath:
        defaultWhatifPath = '/home/vriend/whatif/DO_WHATIF.COM'
        if os.path.exists(defaultWhatifPath):
            whatifPath = defaultWhatifPath
    if not whatifPath:
        _NTmessage("Could not find 'what if'")
    else:
        _NTmessage("........ Found 'what if'")
        whatifPath = strip(whatifPath)
        parametersDict['whatifPath'] = whatifPath
        head, _tail = os.path.split( whatifPath )
        dsspPath = os.path.join( head, 'dssp', 'DSSP.EXE' )
        if not os.path.exists(dsspPath):
            _NTmessage("Could not find 'dssp'")
        else:
            _NTmessage("........ Found 'dssp'")
            parametersDict['dsspPath'] = dsspPath

    time = 0
    try:
        wattosAtTheReady,err  = _NTgetoutput('java Wattos.Utils.Programs.GetEpochTime')
#        _NTmessage("wattosAtTheReady: " + wattosAtTheReady)
#        _NTmessage("err: " + err)
        time = atoi(wattosAtTheReady)
    except:
        pass
#    NTdebug("time: " + `time`)
    if time < 1197298392169: # time at: Mon Dec 10 15:56:33 CET 2007
        _NTmessage("Could not find 'Wattos'")
#        _NTmessage("Failed to get epoch time. This was a test of Wattos installation.'")
    else:
        _NTmessage("........ Found 'wattos'")

    convertPath,err  = _NTgetoutput('which convert')
    if not convertPath:
        _NTwarning("Could not find 'convert' (from ImageMagick)")
        parametersDict['convertPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'convert'")
        parametersDict['convertPath'] = strip(convertPath)

    ghostscriptPath,err  = _NTgetoutput('which gs')
    if not ghostscriptPath:
        _NTwarning("Could not find 'ghostscript' (from ImageMagick)")
        parametersDict['ghostscriptPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'ghostscript'")
        parametersDict['ghostscriptPath'] = strip(ghostscriptPath)

    ps2pdfPath,err  = _NTgetoutput('which ps2pdf14')
    if not ps2pdfPath:
        _NTwarning("Could not find 'ps2pdf' (from Ghostscript)")
        parametersDict['ps2pdfPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'ps2pdf'")
        parametersDict['ps2pdfPath'] = strip(ps2pdfPath)

    molmolPath,err  = _NTgetoutput('which molmol')
    if not molmolPath:
        _NTmessage("Could not find 'molmol'")
        parametersDict['molmolPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'molmol'")
        parametersDict['molmolPath'] = strip(molmolPath)

    povrayPath,err  = _NTgetoutput('which povray')
    if not povrayPath:
        _NTmessage("Could not find 'povray'")
        parametersDict['povrayPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'povray'")
        parametersDict['povrayPath'] = strip(povrayPath)

    talosPath,err  = _NTgetoutput('which talos+')
    if not talosPath:
        _NTmessage("Could not find 'talos'")
        parametersDict['talosPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'talos'")
        parametersDict['talosPath'] = strip(talosPath)

    # TODO: enable real location finder. This just works for JFD but shouldn't bother
    # others.
    pyMolPath,err  = ('/sw/lib/pymol-py25', None)
    if not os.path.exists(pyMolPath):
        pyMolPath = '/sw/lib/pymol-py26' # for AWSS
        if not os.path.exists(pyMolPath):
            pyMolPath = None
    if not pyMolPath:
        _NTmessage("Could not find 'pymol' code (optional)")
        parametersDict['pyMolPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'pymol' code")
        parametersDict['pyMolPath'] = strip(pyMolPath)

    # TODO: enable real location finder. This just works for JFD but shouldn't bother
    # others.
#    yasaraBasePath,err  = ('/Applications/YASARA-dynamics 8.2.3.app', None)
    yasaraBasePath,err  = ('/Applications/YASARA.app', None)
    if not os.path.exists(yasaraBasePath):
        _NTmessage("Could not find 'Yasara' code (optional)")
        parametersDict['yasaraPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'Yasara' code")
        parametersDict['yasaraPath'] = strip(yasaraBasePath)

    # Just to get a message to user; not important.
    pyMolBinPath,err  = _NTgetoutput('which pymol')
    if not pyMolBinPath:
        pyMolBinPath = '//sw/bin/pymol'
        if not os.path.exists(pyMolBinPath):
            pyMolBinPath = None
    if not pyMolBinPath:
        _NTmessage("Could not find 'pymol' binary (optional)")
#        parametersDict['pyMolBinPath']  = PLEASE_ADD_EXECUTABLE_HERE
    else:
        _NTmessage("........ Found 'pymol' binary")
#        parametersDict['pyMolBinPath'] = strip(pyMolPath)


#    userShell = os.environ.get('SHELL')
#    Better not use the above as this gives on JFD's mac: /bin/bash and actually
#    use tcsh. Better ask a question once.
    answer = None
    print ''
    while answer not in ["y","n"]:
        answer = raw_input("Do you use tcsh/csh [y] or bash/sh/ksh/zsh/ash etc. [n]; please enter y or n:")
    isTcsh = answer == "y"

    _writeCingShellFile(isTcsh)
    _NTmessage("TODO: configure MolProbity by running it's setup.sh") # TODO:
