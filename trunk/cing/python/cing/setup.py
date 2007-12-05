# Please note the lack of imports here to cing specific code.
# The idea is that this script runs without PYTHONPATH being set yet.
from string import strip
import sys
import os

"""
python YOUR_CING_PATH_HERE/python/cing/setup.py
E.g.:
python /Users/jd/workspace/cing/python/cing/setup.py

Generates either cing.csh or cing .sh to source in your .cshrc or .bashrc 
(or equivalent) respective file

Adjust if needed.

GV: 16 Sep: added cingBinPath and profitPath
JFD: 27 Nov 2007 removed again.

Uses 'which xplor/profit/$prodir/procheck_nmr.scr/DO_WHATIF.COM' to determine initial 
xplor/profit/procheck/what if executables; make sure they are in your 
path when you run setup. If they are not; you may continue without their 
respective functionalities.
"""

#------------------------------------------------------------------------------------
# generate setup csh or bash script
#------------------------------------------------------------------------------------

CING_SHELL_TEMPLATE = \
'''
#############################################
# adjust these, if needed 
#############################################
%(export)s  xplorPath%(equals)s%(xplorPath)s
%(export)s  profitPath%(equals)s%(profitPath)s
%(export)s  procheckPath%(equals)s%(procheckPath)s
%(export)s  whatifPath%(equals)s%(whatifPath)s
#############################################
# No changes needed below this line.
#############################################
%(export)s  CINGROOT%(equals)s%(cingRoot)s

if %(conditional)s then
    %(export)s PYTHONPATH%(equals)s.:$CINGROOT/python:$PYTHONPATH
else
    %(export)s PYTHONPATH%(equals)s.:$CINGROOT/python
%(close_if)s

alias cing 'python $CINGROOT/python/cing/main.py'

'''
#------------------------------------------------------------------------------------

######################################################################################################
# This code is repeated in __init__.py and setup.py please keep it sync-ed
cingPythonCingDir = os.path.split(os.path.abspath(__file__))[0]
# The path to add to your PYTHONPATH thru the settings script generated by cing.core.setup.py
cingPythonDir = os.path.split(cingPythonCingDir)[0]
# Now a very important variable used through out the code. Even though the
# environment variable CINGROOT is defined the same this is the prefered 
# source for the info within the CING python code.
cingRoot = os.path.split(cingPythonDir)[0]
#printDebug("cingRoot        : " + cingRoot)
######################################################################################################

######################################################################################################
# This code is repeated in cing/setup.py and cing/Libs/NTutils.py please keep it sync-ed
######################################################################################################
def NTgetoutput( cmd ):
    """Return output from command as (stdout,sterr) tuple"""
    inp,out,err = os.popen3( cmd )
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
def printWarning(msg):
    print "WARNING:",msg
def printMessage(msg):
    print msg

def _writeCingShellFile(isTcsh):
    '''Generate the Cing Shell file for csh or bash'''
    if isTcsh:
        parametersDict['export'] = 'setenv'
        parametersDict['equals'] = ' '
        parametersDict['conditional'] = '($?PYTHONPATH)'
        parametersDict['close_if'] = 'endif'
        cname = 'cing.csh'
    else:
        parametersDict['export'] = 'export'
        parametersDict['equals'] = '='
        parametersDict['conditional'] = '[ ! -z "${PYTHONPATH}" ];'
        parametersDict['close_if'] = 'fi'
        cname = 'cing.sh'
    text = CING_SHELL_TEMPLATE % parametersDict
    if isTcsh:
        text += "\nrehash\n"
    cname = os.path.join( cingRoot, cname )
    fp = open(cname,'w')
    fp.write(text)
    fp.close()
    print '==> Done'
    print ' Please check/modify %s' % (cname,)
    print ' Then activate it by including it in your shell settings file (.cshrc or .bashrc)'
#end def
#------------------------------------------------------------------------------------


if __name__ == '__main__':
    
    if not cingRoot:
        print "Failed to derive the CINGROOT from this setup.py script; are there other setup.py or code confusing me here?"
        sys.exit(1)
        
    if not os.path.exists(cingRoot):
        print "The derived CINGROOT doesn't exist: ["  + cingRoot + "]"
        sys.exit(1)

    if not cingPythonDir:
        print "Failed to derive the CING python directory from this setup.py script. No clue why?"
        sys.exit(1)
        
    parametersDict = {}
    parametersDict['cingPythonDir'] = cingPythonDir
    parametersDict['cingRoot']      = cingRoot
    
    xplorPath,err  = NTgetoutput('which xplor')
    if not xplorPath:
        printWarning("Couldn't find 'xplor'")
        parametersDict['xplorPath']  = "PLEASE_ADD_EXECUTABLE_HERE"
    else:
        printMessage("Found 'xplor'")
        parametersDict['xplorPath']  = strip(xplorPath)
    
    profitPath,err  = NTgetoutput('which profit')
    if not profitPath:
        printWarning("Couldn't find 'profit'")
        parametersDict['profitPath']  = "PLEASE_ADD_EXECUTABLE_HERE"
    else:
        printMessage("Found 'profit'")
        parametersDict['profitPath'] = strip(profitPath)
       
#    procheckPath,err  = NTgetoutput('which $prodir/procheck_nmr.scr')
    if os.environ.has_key("prodir"):
        procheckPath = os.path.join( os.environ["prodir"], "procheck_nmr.scr")
        if not os.path.exists(procheckPath):
            printWarning("Found the system variable prodir but the script below wasn't found")
            printWarning( procheckPath )
            printWarning("Couldn't find 'procheck_nmr'")
            parametersDict['procheckPath']  = "PLEASE_ADD_EXECUTABLE_HERE"        
        else:
            printMessage("Found 'procheck_nmr'")
            parametersDict['procheckPath'] = procheckPath
    else:
        printWarning("Couldn't find 'procheck_nmr'")
        parametersDict['procheckPath']  = "PLEASE_ADD_EXECUTABLE_HERE"        
    
    whatifPath,err  = NTgetoutput('which DO_WHATIF.COM')
    if not whatifPath:
        printWarning("Couldn't find 'what if'")   
        parametersDict['whatifPath']  = "PLEASE_ADD_EXECUTABLE_HERE"
    else:
        printMessage("Found 'what if'")
        parametersDict['whatifPath'] = strip(whatifPath)
    
#    userShell = os.environ.get('SHELL')
#    Better not use the above as this gives on JFD's mac: /bin/bash and actually
#    use tcsh. Better ask a question once.
    answer = None     
    while answer not in ["y","n"]:
        answer = raw_input("Do you use tcsh/csh [y] or bash/sh/ksh/zsh/ash etc. [n]; please enter y or n:")
    isTcsh = answer == "y"
        
    _writeCingShellFile(isTcsh)