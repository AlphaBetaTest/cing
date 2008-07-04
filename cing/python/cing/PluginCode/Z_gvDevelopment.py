"""

GVprocheck( ranges=None, verbose = True )

Molecule:
    procheck: <Procheck> object

Residue
    procheck: NTdict instance with procheck values for this residue

"""

from cing.Libs.AwkLike import AwkLike
from cing.Libs.NTutils import *
from cing.core.parameters import cingPaths
import cing

import os

def procheckString2float( string ):
    """Convert a string to float, return None in case of value of 999.90
    """
    result = float( string )
    if result == 999.90:
        return None
    else:
        return result
    #end if
#end def


class gvProcheck:
    #TODO: subclass this from ExecuteProgram
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
      55GLY A  62 T-147.73 -20.13-166.50 999.90 999.90 999.90 999.90  -0.87   0.00 999.90   0.00  0.000  0.000 11 38  0.000  0.000
      56ASP A  63 e -78.77 161.06-173.97 -56.24 -71.93 999.90 999.90  -0.76   0.00  34.42   0.00  0.000  0.000 13 50  0.000  0.000
      57ARG A  64 E-104.07 124.65 166.81 177.50-170.21 179.43-172.18  -2.12   0.00  37.30   0.00  0.000  0.000 12 56  0.000  0.000
      58VAL A  65 E -87.26 117.24 175.76-157.64 999.90 999.90 999.90  -3.33   0.00  33.46   0.00  0.000  0.000 14 67  0.000  0.000
      59LEU A  66 E -99.01 -36.19-179.02  50.71 149.42 999.90 999.90  -2.74   0.00  31.00   0.00  0.000  0.000 13 50  0.000  0.000
      95PRO!A 102   -69.35 999.90 999.90 -24.86 999.90 999.90 999.90   0.00   0.00  37.72   0.00  0.000  0.000  4 13  0.000  0.000
      96TYR!B 205   999.90 -55.02-171.34-143.34 -89.71 999.90 999.90   0.00   0.00  34.80   0.00  0.000  0.000  2  5  0.000  0.000
      97LEU B 206    61.37 179.80 171.30-145.66  66.98 999.90 999.90   0.00   0.00  31.07   0.00  0.000  0.000  3  5  0.000  0.000
    """
    procheckDefs = NTdict(
    #   field       (startChar, endChar, conversionFunction)
        line      = (  0,  4, int ),
        resName   = (  4,  7, str ),
        chain     = (  8,  9, str ),
        resNum    = ( 10, 13, int ),
        secStruct = ( 14, 15, str ),
        PHI       = ( 15, 22, procheckString2float ),
        PSI       = ( 22, 29, procheckString2float ),
        OMEGA     = ( 29, 36, procheckString2float ),
        CHI1      = ( 36, 43, procheckString2float ),
        CHI2      = ( 43, 50, procheckString2float ),
        CHI3      = ( 50, 57, procheckString2float ),
        CHI4      = ( 57, 64, procheckString2float )
    )

    def __init__(self, project ):
        """
        Procheck class allows running procheck_nmr and parsing of results
        """
        self.molecule     = project.molecule
        self.rootPath     = project.mkdir( project.molecule.name, project.moleculeDirectories.procheck  )
#        self.runProcheck  = ExecuteProgram( cing.paths.procheck_nmr,
#                                            rootPath = self.rootPath,
#                                            redirectOutput= False
#                                          )
        self.ranges  = None
        self.summary = None
    #end def

    def run(self, ranges=None ):
        NTmessage('==> Running procheck_nmr, ranges %s, results in "%s" ...', ranges, self.rootPath)

        # Convert the ranges and translate into procheck_nmr format
        selectedResidues = self.molecule.ranges2list( ranges )
        NTsort(selectedResidues, 'resNum', inplace=True)
        # reduce this sorted list to pairs start, stop
        self.ranges = selectedResidues[0:1]
        for i in range(0,len(selectedResidues)-1):
            if ((selectedResidues[i].resNum < selectedResidues[i+1].resNum - 1) or
                (selectedResidues[i].chain != selectedResidues[i+1].chain)
               ):
                self.ranges.append(selectedResidues[i])
                self.ranges.append(selectedResidues[i+1])
            #end if
        #end for
        self.ranges.append(selectedResidues[-1])
        NTdebug( 'Procheck ranges %d', self.ranges )
        #generate the ranges file
        path = os.path.join( self.rootPath, 'ranges')
        fp = open( path, 'w' )
        for i in range(0,len(self.ranges),2):
            fprintf( fp, 'RESIDUES %3d %2s  %3d %2s\n', self.ranges[i].resNum, self.ranges[i].chain.name,
                                                        self.ranges[i+1].resNum, self.ranges[i+1].chain.name
                   )
        #end for
        fp.close()

        #export a PDB file
        path = os.path.join( self.rootPath, self.molecule.name + '.pdb')
        #print path
        self.molecule.toPDBfile( path, convention=cing.PDB )

        # run procehck
        runProcheck  = ExecuteProgram( cingPaths.procheck_nmr,
                                       rootPath = self.rootPath,
                                       redirectOutput= True
                                    )
        runProcheck( self.molecule.name +'.pdb ranges' )
        del( runProcheck )

        # Parse results
        self.parseResult()
    #end def

    def _parseProcheckLine( self, line ):
        """
        Internal routine to parse a single line
        Return result, which is a dict type or None
        on error (i.e. too short line)
        """
    #    print ">>", line
        result = {}
        if (len(line) >= 64):
            for field,fieldDef in self.procheckDefs.iteritems():
                c1,c2,func = fieldDef
                result[ field ] = func(line[c1:c2])
            #end for
        else:
            return None
        #end if

    #    print result
        return result
    #end def

    def parseResult( self ):
        """
        Get summary

        Parse procheck .rin files and store result in procheck NTdict
        of each residue of mol

        """
        path = os.path.join( self.rootPath, sprintf('%s.sum', self.molecule.name) )
        fp = open( path, 'r' )
        if not fp:
            NTerror('gvProcheck.parseResult: %s not found', path)
        else:
            self.summary = ''.join(fp.readlines())
            fp.close()
        #end if

        for i in range(1,self.molecule.modelCount+1):
            path = os.path.join( self.rootPath, sprintf('%s_%03d.rin', self.molecule.name, i) )
            #print '> parsing >', path

            for line in AwkLike( path, minLength = 64, commentString = "#" ):
                result = self._parseProcheckLine( line.dollar[0] )
                chain   = result['chain']
                resNum  = result['resNum']
                residue = self.molecule.decodeNameTuple((cing.PDB,chain,resNum,None))
                if not residue:
                    NTerror('Procheck.parseResult: residue not found (%s,%d)', chain, resNum )
                else:

                    residue.setdefault( 'procheck', NTstruct() )
                    for field,value in result.iteritems():
                        residue.procheck.setdefault( field, NTlist() )
                        residue.procheck[field].append( value )
                    #end for
                #end if
                del( result )
            #end for
        #end for
    #end def
#end class

def procheck_old( project, ranges=None ):
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

    pcheck = gvProcheck( project )
    if not pcheck: return None

    pcheck.run( ranges=ranges )
    project.molecule.procheck = pcheck

    return project.molecule.procheck
#end def

# register the functions
methods  = [(procheck_old, None)
           ]
#saves    = []
#restores = []
#exports  = []
