"""
Adds procheck methods
----------------  Methods  ----------------


procheck( ranges=None, verbose = True )  


----------------  Attributes generated  ----------------


Molecule:
    procheck: <Procheck> object 
    
Residue
    procheck: NTdict instance with procheck values for this residue 

"""
from cing import cingPythonCingDir
from cing.Libs.AwkLike import AwkLike
from cing.Libs.NTutils import ExecuteProgram
from cing.Libs.NTutils import NTdict
from cing.Libs.NTutils import NTerror
from cing.Libs.NTutils import NTlist
from cing.Libs.NTutils import NTsort
from cing.Libs.NTutils import fprintf
from cing.Libs.NTutils import printCodeError
from cing.Libs.NTutils import printDebug
from cing.Libs.NTutils import printError
from cing.Libs.NTutils import printMessage
from cing.Libs.NTutils import printWarning
from cing.core.constants import IUPAC
from cing.core.parameters import cingPaths
import os

def procheckString2float(string):
    """Convert a string to float, return None in case of value of 999.90"""
    result = float(string)
    if result > 999.8 and result < 999.99:
        return None
    return result


class Procheck:
    """
    From Jurgen:
 
    Column id 
    ^ Fortran variable
    ^ ^        Explanation
    ##############################
    ###################################################
    1 NXRES    residue number in procheck
    2 AA3      residue name
    3 BRKSYM   chain id as in PDB file
    4 SEQBCD   resdiue id as in PDB file??
    5 SUMMPL   secondary structure classification (DSSP?)
    6 MCANGS 1 phi
    7 MCANGS 2 psi
    8 MCANGS 3 omega 
    9 SCANGS 1 chi 1
    0 SCANGS 2 chi 2
    1 SCANGS 3 chi 3
    2 SCANGS 4 chi 4
    3 HBONDE   Hydrogen bond energy
    4 DSDSTS ? statistics?
    5 MCANGS ?
    6 BVALUE   Crystallographic B factor
    7 MCBVAL   Mainchain B value
    8 SCBVAL   Sidechain B value
    9 OOIS 1 ?
    0 OOIS 2 ?
    1 MCBSTD Main chain bond standard deviation?
    2 SCBSTD Side chain bond standard deviation?
    
    
    #0000000000000000000000000000000000000000000000000000000000000000000000
                    phi   psi    omega  chi1   chi2   chi3   chi4   hb     dsdsts mcang
      55GLY A  62 T-147.73 -20.13-166.50 999.90 999.90 999.90 999.90  -0.87   0.00 999.90   0.00  0.000  0.000 11 38  0.000  0.000
      56ASP A  63 e -78.77 161.06-173.97 -56.24 -71.93 999.90 999.90  -0.76   0.00  34.42   0.00  0.000  0.000 13 50  0.000  0.000
      57ARG A  64 E-104.07 124.65 166.81 177.50-170.21 179.43-172.18  -2.12   0.00  37.30   0.00  0.000  0.000 12 56  0.000  0.000
      58VAL A  65 E -87.26 117.24 175.76-157.64 999.90 999.90 999.90  -3.33   0.00  33.46   0.00  0.000  0.000 14 67  0.000  0.000
      59LEU A  66 E -99.01 -36.19-179.02  50.71 149.42 999.90 999.90  -2.74   0.00  31.00   0.00  0.000  0.000 13 50  0.000  0.000
      95PRO!A 102   -69.35 999.90 999.90 -24.86 999.90 999.90 999.90   0.00   0.00  37.72   0.00  0.000  0.000  4 13  0.000  0.000
      96TYR!B 205   999.90 -55.02-171.34-143.34 -89.71 999.90 999.90   0.00   0.00  34.80   0.00  0.000  0.000  2  5  0.000  0.000
      97LEU B 206    61.37 179.80 171.30-145.66  66.98 999.90 999.90   0.00   0.00  31.07   0.00  0.000  0.000  3  5  0.000  0.000
        # 2hgh
      10GLY A 113    74.45  15.22 178.99 999.90 999.90 999.90 999.90  -0.95   0.00 999.90   0.00  0.000  0.000  9 20  0.000  0.000
      11LYS A 114 e -71.09 143.35-173.40-153.49 165.04 174.07  65.99   0.00   0.00  34.73   0.00  0.000  0.000  7 25  0.000  0.000
      12ALA A 115 E-123.24 137.51-174.84 999.90 999.90 999.90 999.90   0.00   0.00  34.69   0.00  0.000  0.000  9 22  0.000  0.000
      13PHE A 116 E-126.20 154.68 179.89 -49.13  80.54 999.90 999.90  -3.08   0.00  35.22   0.00  0.000  0.000 10 21  0.000  0.000
      14LYS A 117 S -66.93 -37.97-173.87-164.02 169.28-166.01  51.19   0.00   0.00  34.94   0.00  0.000  0.000  7 16  0.000  0.000
      15LYS A 118 h-135.63 148.98-170.06 -51.60 -73.02 152.83  37.49   0.00   0.00  34.76   0.00  0.000  0.000  8 19  0.000  0.000
      16HIS A 119 H -66.31 -28.97 177.00  52.90  58.00 999.90 999.90   0.00   0.00  34.07   0.00  0.000  0.000  8 24  0.000  0.000
      17ASN A 120 H -64.88 -30.42 173.13  18.31  58.33 999.90 999.90   0.00   0.00  33.97   0.00  0.000  0.000  7 30  0.000  0.000
      18GLN A 121 H -73.16 -37.55 175.47 -46.40-178.69 -71.05 999.90  -0.83   0.00  34.45   0.00  0.000  0.000  9 30  0.000  0.000
      19LEU A 122 H -61.95 -47.13 175.48 169.01  56.82 999.90 999.90  -1.43   0.00  34.90   0.00  0.000  0.000 13 31  0.000  0.000
      20LYS A 123 H -60.27 -39.32 175.72 -80.80-175.12 167.71 178.94  -2.93   0.00  34.60   0.00  0.000  0.000  9 36  0.000  0.000

    
    .edt file The contents of the .edt file are:

           FORMAT(A1,A5,A3,6(1X,F7.3),2(1X,F7.3),4(1X,F6.2))
           A1  -  Chain-id
           A5  -  Residue number
           A3  -  Residue name
         6F7.3 -  The 6 circular variance values for the phi, psi, chi1,
                  chi2, phi-psi and chi1-chi2 distributions.
         2F7.3 -  Main-chain and side-chain deviations of this residue
                  from the overall mean value
         4F6.2 -  The G-factors for the phi-psi, chi1-chi2, chi1 only,
                  and the overall average.
01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
0    -    1         2         3         4         5         6         7    -    8         9         1     
A 185 ALA   0.000   0.000 999.900 999.900   0.000 999.900   0.500   0.499   0.80 999.90 999.90   0.80
A 186 GLU   0.000   0.002   0.363   0.504   0.001   0.429   0.489   2.949  -0.66   0.75 999.90   0.04
A 187 CYS   0.002   0.000   0.000 999.900   0.001 999.900   0.591   0.585  -0.41 999.90   0.13  -0.14
A 188 HIS   0.001   0.041   0.001   0.000   0.020   0.001   0.836   0.494  -1.69   1.22 999.90  -0.24
A 189 GLN   0.243   0.071   0.164   0.660   0.153   0.362   1.840   6.256  -0.73  -1.05 999.90  -0.89
A 190 ASP   0.001 999.900   0.000   0.001 999.900   0.000   5.329   8.952 999.90  -1.14 999.90  -1.14
B   2 G   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.574 999.90 999.90 999.90   0.00
B   3 G   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.306 999.90 999.90 999.90   0.00
B   4 C   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.076 999.90 999.90 999.90   0.00
B   5 C   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.002 999.90 999.90 999.90   0.00
B   6 A   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.149 999.90 999.90 999.90   0.00
B   7 U   999.900 999.900 999.900 999.900 999.900 999.900   0.000   1.932 999.90 999.90 999.90   0.00
                

    """        
    procheckEnsembleDefs = NTdict(
                          # Keep rucksack from filling up over the years.
    #   field       (startChar, endChar, conversionFunction, store)
#        line      = (  0,  4, int, False ), # unique residue id over all models in NMR ensemble. No need to capture.
        chain     = (0, 1, str, False), 
        resNum    = (1, 5, int, False), 
        resName   = (6, 9, str, False), 
        # ignore 6 cv values and 2 deviation values.
        gfPHIPSI  = (74, 80, procheckString2float, True), 
        gfCHI12   = (81, 87, procheckString2float, True), 
        gfCHI1    = (88, 94, procheckString2float, True), 
        gf        = (95, 101, procheckString2float, True) # note it's zero for nucleic acids.
    )
    procheckDefs = NTdict(
                          # Keep rucksack from filling up over the years.
    #   field       (startChar, endChar, conversionFunction, store)
#        line      = (  0,  4, int, False ), # unique residue id over all models in NMR ensemble. No need to capture.
        resName   = (4, 7, str, False), 
        chain     = (8, 9, str, False), 
        resNum    = (10, 13, int, False), 
        secStruct = (14, 15, str, True), 
        PHI       = (15, 22, procheckString2float, False), # Already calculated internally.
        PSI       = (22, 29, procheckString2float, False), 
        OMEGA     = (29, 36, procheckString2float, False), 
        CHI1      = (36, 43, procheckString2float, False), 
        CHI2      = (43, 50, procheckString2float, False), 
        CHI3      = (50, 57, procheckString2float, False), 
        CHI4      = (57, 64, procheckString2float, False)
    )
    
    def __init__(self, project):
        """
        Procheck class allows running procheck_nmr and parsing of results
        """
        self.project      = project
        self.molecule     = project.molecule
        self.rootPath     = project.mkdir(project.molecule.name, project.moleculeDirectories.procheck)
        self.redirectOutput = True
        if project.parameters.verbose():
            self.redirectOutput=False
#        printDebug("Will redirect procheck output: " + `self.redirectOutput`)
        self.procheck  = ExecuteProgram(cingPaths.procheck_nmr, 
                                            rootPath = self.rootPath, 
                                            redirectOutput= self.redirectOutput
                                          )
        self.aqpc      = ExecuteProgram(cingPaths.aqpc, 
                                    rootPath = self.rootPath, 
                                    redirectOutput= self.redirectOutput
                                          )
        self.ranges = None
    #end def
    
    # Return True on error ( None on success; Python default)
    def run(self, ranges=None, export = True, verbose=True):
        # Convert the ranges and translate into procheck format
        selectedResidues = self.molecule.ranges2list(ranges)
        NTsort(selectedResidues, 'resNum', inplace=True)
        # reduce this sorted list to pairs start, stop
        self.ranges = selectedResidues[0:1]
        for i in range(0, len(selectedResidues)-1):
            if ((selectedResidues[i].resNum < selectedResidues[i+1].resNum - 1) or 
                (selectedResidues[i].chain != selectedResidues[i+1].chain)
               ):
                self.ranges.append(selectedResidues[i])
                self.ranges.append(selectedResidues[i+1])
            #end if
        #end for        
        self.ranges.append(selectedResidues[-1])
#        print '>ranges (just the boundaries)', self.ranges
        #generate the ranges file
        path = os.path.join(self.rootPath, 'ranges')
        fp = open(path, 'w')
        for i in range(0, len(self.ranges), 2):
            singleRange = 'RESIDUES %3d %2s  %3d %2s' % (self.ranges[i].resNum, self.ranges[i].chain.name, 
                                                            self.ranges[i+1].resNum, self.ranges[i+1].chain.name)
            fprintf(fp, singleRange+"\n")
            print ">range: " + singleRange
        fp.close()

        pcNmrParameterFile = os.path.join(cingPythonCingDir, 'PluginCode', 'data', 'procheck_nmr.prm')
        pcNmrParameterFileDestination = os.path.join(self.rootPath, 'procheck_nmr.prm')
        if os.path.exists(pcNmrParameterFileDestination):
            printDebug("Removing existing pcNmrParameterFileDestination:"+ pcNmrParameterFileDestination)
            os.unlink(pcNmrParameterFileDestination)
        printDebug("Copying "+pcNmrParameterFile+" to: " + pcNmrParameterFileDestination)
        if os.link(pcNmrParameterFile, pcNmrParameterFileDestination):
            printError("Failed to copy from " +pcNmrParameterFile+" to: " + pcNmrParameterFileDestination)
            return True
        
        path = os.path.join(self.rootPath, self.molecule.name + '.pdb')
        if export:
#            project.molecule.modelCount
            self.molecule.toPDBfile(path, convention=IUPAC, verbose=verbose)
            
        canAqpc = True
        # Save restraints for Aqua
        if self.project.export2aqua():
            canAqpc = False
            printWarning("Failed to export restraints to Aqua; will run pc without restraints")
        else:
            hasRestraints = False
            for extensionRestraintFile in [ "noe", "tor" ]:
                srcDir = os.path.join(self.project.rootPath(self.project.name), self.project.directories.aqua )
                if not os.path.exists(srcDir):
                    printCodeError("Aqua export dir is absent")
                    return True
                fileName = self.project.name +'.' + extensionRestraintFile
                path = os.path.join(srcDir, fileName )                
                if not os.path.exists(path):                    
                    printDebug("No "+ path+" file found (in Aqua export dir)")
                    pass
                else:
                    # Map from Aqua per project file to Cing per molecule file.
                    dstFileName = self.molecule.name + '.' + extensionRestraintFile
                    dstPath = os.path.join( self.rootPath, dstFileName )
                    if os.path.exists(dstPath):
                        printDebug("Removing existing copy: " + dstPath)    
                        os.unlink(dstPath)
                    printDebug("Trying to copy from: " + path+" to: "+dstPath)
                    if os.link(path, dstPath):
                        printCodeError("Failed to copy from: " + path+" to: "+self.rootPath)
                        return True
                    hasRestraints = True
            # run aqpc 
            if not canAqpc:
                printWarning("Skipping aqpc because failed to convert restraints to Aqua")
            elif not hasRestraints:
                printWarning("Skipping qapc because no Aqua restraints were copied for Aqua")
            else:
                printMessage("Trying aqpc")
                if self.aqpc( '-r6sum 1 ' + self.molecule.name + '.pdb'):
                    printCodeError("Failed to run aqpc; please consult the log file aqpc.log etc. in the molecules procheck directory.")
                    return True
                else:
                    printMessage("Finished aqpc successfully")
                    
        printMessage("Trying pc")
        if self.procheck(self.molecule.name +'.pdb ranges'):
            printError("Failed to run pc; please consult the log file (.log etc). in the molecules procheck directory.")
            return True
        printMessage("Finished procheck_nmr successfully")
        self.parseResult()
        return True
    #end def
    
    
    def _parseProcheckLine(self, line, defs):
        """
        Internal routine to parse a single line
        Return result, which is a dict type or None
        on error (i.e. too short line)
 e.g.   field       (startChar, endChar, conversionFunction)
        resName   = (  4,  7, str ),
        """
        result = {}
        if len(line) < 65:
            return None
        for field, fieldDef in defs.iteritems():
            c1, c2, func, dummyStore = fieldDef
            result[ field ] = func(line[c1:c2]) 
        return result
    #end def
    
    def parseResult(self):
        """
        Parse procheck files and store result in procheck NTdict
        of each residue of mol
        """
        modelCount = self.molecule.modelCount
        printMessage("Parse procheck files and store result in each residue for " + `modelCount` + " models")
        for i in range(1, modelCount+1):
            path = os.path.join(self.rootPath, '%s_%03d.rin' % (self.molecule.name, i))           
#            print '> parsing rin >', path
    
            for line in AwkLike(path, minLength = 64, commentString = "#"):
                result = self._parseProcheckLine(line.dollar[0], self.procheckDefs)
                if not result:
                    printError("Failed to parse procheck rin file the below line; giving up.")
                    printError(line.dollar[0])
                    return 
                chain   = result['chain']
                resNum  = result['resNum']
                residue = self.molecule.decodeNameTuple((None, chain, resNum, None))
                if not residue:
                    printError('in Procheck.parseResult: residue not found (%s,%d); giving up.' % (chain, resNum))
                    return
                residue.setdefault('procheck', NTdict())
                for field, value in result.iteritems():
                    if not self.procheckDefs[field][3]: # Checking store parameter.
                        continue
                    # Insert for key: "field" if missing an zero lenght list.
                    residue.procheck.setdefault(field, NTlist()) 
                    residue.procheck[field].append(value)
#                del( result ) # redundant to remove reference to this local variable.
            #end for
        #end for
        
        path = os.path.join(self.rootPath, '%s.edt' % self.molecule.name)           
        print '> parsing edt >', path

        for line in AwkLike(path, minLength = 64, commentString = "#"):
            result = self._parseProcheckLine(line.dollar[0], self.procheckEnsembleDefs)
            if not result:
                printError("Failed to parse procheck edt file the below line; giving up.")
                printError(line.dollar[0])
                return 
            chain   = result['chain']
            resNum  = result['resNum']
            residue = self.molecule.decodeNameTuple((None, chain, resNum, None))
            if not residue:
                printError('in Procheck.parseResult: residue not found (%s,%d); giving up.' % (chain, resNum))
                return
            residue.setdefault('procheck', NTdict())
            for field, value in result.iteritems():
                if not self.procheckEnsembleDefs[field][3]: # Checking store parameter.
                    continue
#                residue.procheck.setdefault( field, value ) 
                residue.procheck[field] = value 
        #end for
    #end def    
#end class

def procheck(project, ranges=None, verbose=True):
    """
    Adds <Procheck> instance to molecule. Run procheck and parse result
    """
    if not project.molecule:
        NTerror('ERROR procheck: no molecule defined\n')
        return None
    #end if
    
    if project.molecule.has_key('procheck'):
        del(project.molecule.procheck)
    #end if
    
    pcheck = Procheck(project)
    if not pcheck:
        printError("Failed to get procheck instance of project") 
        return None
    
    pcheck.run(ranges=ranges, verbose=verbose)
    project.molecule.procheck = pcheck
    
    return project.molecule.procheck
#end def

# register the functions
methods  = [(procheck, None)
           ]
#saves    = []
#restores = []
#exports  = []
