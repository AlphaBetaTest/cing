"""
Adds initialize/import/export from/to PDB files


Methods:
    Molecule.importFromPDB( pdbFile, convention='PDB')   :
        Import coordinates from pdbFile
        convention eq PDB, CYANA, CYANA2 or XPLOR
        return molecule or None on error

    Molecule.PDB2Molecule(pdbFile, moleculeName, convention, nmodels)   :
        Initialize  from pdbFile
        Return molecule instance
        convention eq PDB, CYANA, CYANA2 or XPLOR
        staticmethod

    Project.initPDB( pdbFile, convention ):
        initialize from pdbFile, import coordinates
        convention = PDB, CYANA, CYANA2 or XPLOR

    Project.importPDB( pdbFile, convention ):
        import coordinates from pdbFile
        convention = PDB, CYANA, CYANA2 or XPLOR

    Project.export2PDB( pdbFile ):
        export to pdbFile

Speed check: 103.609s for pdbParser.importCoordinates: <Molecule "pdb2k0e" (C:1,R:152,A:2647,M:160)>
"""
from cing.Libs import PyMMLib
from cing.Libs.NTutils import NTcodeerror
from cing.Libs.NTutils import NTdebug
from cing.Libs.NTutils import NTdetail
from cing.Libs.NTutils import NTerror
from cing.Libs.NTutils import NTmessage
from cing.Libs.NTutils import NTpath
from cing.Libs.NTutils import NTtree
from cing.Libs.NTutils import sprintf
from cing.core.constants import INTERNAL
from cing.core.constants import IUPAC
from cing.core.molecule import Molecule
from cing.core.molecule import getNextAvailableChainId
from cing.core.molecule import isValidChainId
from cing.core.molecule import unmatchedAtomByResDictToString
from cing.core.MatchGame import MatchGame
import os

#==============================================================================
# PDB stuff
#==============================================================================
def importFromPDB(molecule, pdbFile, convention = IUPAC, nmodels = None, allowNonStandardResidue = True)   :
    """Import coordinates from pdbFile (optionally: first nmodels)
       convention e.g. PDB, CYANA, CYANA2, XPLOR, IUPAC

       return molecule or None on error
    """
    if not molecule: 
        return None

    parser = pdbParser(pdbFile, convention = convention)
    if not parser:
        return None
    parser.map2molecule(molecule)
    parser.importCoordinates(nmodels = nmodels)
    return molecule
#end def
# Add as a method to Molecule class
Molecule.importFromPDB = importFromPDB



class pdbParser:
    """
    Class to parse the pdb file and import into molecule instance
    Should handle all nitty gritty (sorry for the discriminatory derogative) details such as 
    HIS/ARG/LYS/GLU/ASP/(R)Ade/(R)Cyt/(R)Gua and Cyana1.x related issues

    Steps:
    - Parse the pdbFile into records using PyMMlib.
    - Assemble a tree from chn's,res's,atm's, map records back to atm entries (_records2tree).
    - Map res's and atm's to CING db. Convert the idiocracies in the process. (_matchResidue2Cing and _matchAtom2Cing)
    - Optionally: generate a molecule from chn,res's
    - Map atm's to atoms of molecule.
    - Import the coordinates.

    The allowNonStandardResidue determines if the non-standard residues and atoms are read. If so they will be shown as
    a regular message. Otherwise they will be shown as a warning. Just like MolMol does; the unknown atoms per residue.
    See the image at: http://code.google.com/p/cing/issues/detail?id=126#c4
    
                             atom<->residue->chain<->molecule<-self
                              |
    self->tree<->chn<->res<->atm<-record<-self
                       |      |
               ResidueDef<->AtomDef

    """
    def __init__(self, pdbFile, convention = IUPAC, patchAtomNames = True, skipWaters = False, allowNonStandardResidue = True):

        self.pdbFile = pdbFile
        self.convention = convention
        self.patchAtomNames = patchAtomNames
        self.skipWaters = skipWaters
        self.allowNonStandardResidue = allowNonStandardResidue
        self.matchGame = MatchGame(patchAtomNames = patchAtomNames, skipWaters = skipWaters, allowNonStandardResidue = allowNonStandardResidue)
        
        if not os.path.exists(pdbFile):
            NTerror('pdbParser: missing PDB-file "%s"', pdbFile)
            return None

        NTdetail('==> Parsing pdbFile "%s" ... ', pdbFile)

        self.pdbRecords = PyMMLib.PDBFile(pdbFile)
        if not self.pdbRecords:
            NTerror('pdbParser: parsing PDB-file "%s"', pdbFile)
            return None
        #end if

        # parsing storage
        self._records2tree()
        self._matchResiduesAndAtoms()
        self.molecule = None
    #end def

    def _records2tree(self):
        """Convert the pdbRecords in a tree-structure. Really a HoHoH; Hash of...
        """
        NTdebug("Now in _records2tree")
        self.tree = NTtree('tree') # Tree like structure of pdbFile
        chn = None
        res = None
        atm = None
        self.modelCount = 0
        atomDict = {}

        mapChainId = {} # Keep track of mappings between input and CING when they're not the same.
        chainIdListAlreadyUsed = [] # simpler list.
        
        atmCount = 0
        foundModel = False
        for record in self.pdbRecords:
            recordName = record._name.strip()
            if recordName == "MODEL":
                foundModel = True
                continue
            if recordName == "ENDMDL":
                self.modelCount += 1

            if recordName == "ATOM" or recordName == "HETATM":

                # Not all PDB files have chainID's !@%^&*
                # They do; if none returned then take the space that is always present!
                # JFD adds: take a look at 1ai0 
                #    It features chain ids A thru F but also several residues with a ' ' for the chain id.
                #    Luckily the residues all have non-overlapping numbers. So let's program against 
                #    this study case. Might have to be optimized.
                chainId = ' '
                if record.has_key('chainID'):
                    chainId = record.chainID
                if mapChainId.has_key(chainId):
                    chainId = mapChainId[chainId]
                if not isValidChainId(chainId):                    
                    chainIdNew = getNextAvailableChainId(chainIdListAlreadyUsed = chainIdListAlreadyUsed)
                    mapChainId[chainId] = chainIdNew
                    chainId = chainIdNew
                    
                resName = record.resName.strip()
                resNum = record.resSeq
                fullResName = resName + str(resNum)

                atmName = record.name.strip()

                t = (chainId, fullResName, atmName)

                if atomDict.has_key(t):
                    atm = atomDict[t]
                else:

                    if not self.tree.has_key(chainId):
                        chn = self.tree.addChild(name = chainId)
                        if chainId in chainIdListAlreadyUsed:
                            NTcodeerror("list out of sync in _records2tree")
                        else:
                            chainIdListAlreadyUsed.append(chainId) # simpler object for getNextAvailableChainId
                    else:
                        chn = self.tree[chainId]
                    #end if
                    if not chn:
                        NTdebug('pdbParser._records2tree: strange, we should not have a None for chain; record %s', record)
                        continue
                    #end if

                    if not chn.has_key(fullResName):
                        res = chn.addChild(name = fullResName, resName = resName, resNum = resNum)
                    else:
                        res = chn[fullResName]
                    #end if
                    if not res:
                        NTdebug('pdbParser._records2tree: strange, we should not have a None for residue; record %s', record)
                        continue
                    #end if

                    if not res.has_key(atmName):
                        atm = res.addChild(atmName)
                    else:
                        atm = res[atmName]
                    #end if
                    if not atm:
                        NTdebug('pdbParser._records2tree: strange, we should not have a None for atom; record %s', record)
                        continue
                    #end if
                    atomDict[t] = atm
#                    print chn, res,atm
                #end if

                # Make a reference to the tree
                record.atm = atm
                atmCount += 1
            #end if
        #end for
        if not foundModel: # X-rays do not have MODEL record
            self.modelCount = 1

        NTdebug('end pdbParser._records2tree: parsed %d pdb records, %d models', atmCount, self.modelCount)
    #end def

    def _matchResiduesAndAtoms(self):
        """
        Match residues and Atoms in the tree to CING db using self.convention
        """
        NTdebug("Now in _matchResiduesAndAtoms")
        unmatchedAtomByResDict = {}
#        unmatchedResDict = {}
        for res in self.tree.subNodes(depth = 2):
            self.matchGame.matchResidue2Cing(res)
            for atm in res:
                if not self.matchGame.matchAtom2Cing(atm):                    
                    if not unmatchedAtomByResDict.has_key(res.resName):
                        unmatchedAtomByResDict[ res.resName ] = ([], [])
                    atmList = unmatchedAtomByResDict[res.resName][0] 
                    resNumList = unmatchedAtomByResDict[res.resName][1] 
                    if atm.name not in atmList:
                        atmList.append(atm.name)
                    if res.resNum not in resNumList:
                        resNumList.append(res.resNum)
        
                    if not self.allowNonStandardResidue:
                        atm.skip = True
                        continue                        

#                   aName = moveFirstDigitToEnd(atm.name) # worry about this?
                    atm.db = res.db.appendAtomDef(atm.name)
                    if not atm.db:
                        NTcodeerror("Should have been possible to add a non-standard atom %s to the residue %s" % (atm.name, res.resName))
                        continue        
                                            
        msg = "Non-standard (residues and their) atoms"
        if self.allowNonStandardResidue:
            msg += " to add:\n"
        else:
            msg += " to skip:\n"
        
        if unmatchedAtomByResDict:
            msg += unmatchedAtomByResDictToString(unmatchedAtomByResDict)
            if self.allowNonStandardResidue:
                NTmessage(msg)
            else:
                NTerror(msg)             
    #end def

    def initMolecule(self, moleculeName):
        """Initialize new Molecule instance from the tree.
        Return Molecule on None on error.
        """
        mol = Molecule(name = moleculeName)

        # The self.tree contains a tree-like representation of the pdb-records
        for ch in self.tree:
            chain = mol.addChain(name = ch.name)
            for res in ch:
#                print '>', ch, res, res.skip, res.db
                if not res.skip and res.db != None:
                    residue = chain.addResidue(res.db.name, res.resNum)
                    residue.addAllAtoms()
                #end if
            #end for
        #end for
#        NTdebug('pdbParser.initMolecule: %s', mol)
        self.map2molecule(mol)
        return mol
    #end for

    def map2molecule(self, molecule):
        """
        Map the tree to CING molecule instance.
        """
        
        unmatchedAtomByResDict = {}
                        
        for chn in self.tree:
            for res in chn:
#                NTdebug("map2molecule res: %s" % res)
                if res.skip or (not res.db):
                    continue
                for atm in res:
                    atm.atom = None
                    if atm.skip or (not atm.db):
#                        NTerror("pdbParser#map2molecule was flagged before right?")
                        continue
                    t = (IUPAC, chn.name, res.resNum, atm.db.name)
                    atm.atom = molecule.decodeNameTuple(t)                      
                    if not atm.atom: # for the non-standard residues and atoms.
                        t = (INTERNAL, chn.name, res.resNum, atm.db.name)
                        atm.atom = molecule.decodeNameTuple(t)                      
                    if not atm.atom:
                        # JFD: Report all together now.
                        if not unmatchedAtomByResDict.has_key(res.resName):
                            unmatchedAtomByResDict[ res.resName ] = ([], [])
                        atmList = unmatchedAtomByResDict[res.resName][0]
                        resNumList = unmatchedAtomByResDict[res.resName][1]
                        if atm.name not in atmList:
                            atmList.append(atm.name)
                        if res.resNum not in resNumList:
                            resNumList.append(res.resNum)                            
                        #end if
                    #end if
                #end for
            #end for
        #end for
        self.molecule = molecule
        
        if unmatchedAtomByResDict:
            msg = "pdbParser.map2molecule: Strange! ERROR mapping atom for:\n"
            msg += unmatchedAtomByResDictToString(unmatchedAtomByResDict)
            NTcodeerror(msg)             
    #end def

    def importCoordinates(self, nmodels = None, update = True):
        """
        Import coordinates into self.molecule.
        Optionally use only first nmodels.
        Optionally do not update dihedrals, mean-coordiates, .. (Be careful; only intended for conversion
        purposes).

        Return True on error
        """

        if not self.molecule:
            NTerror('pdbParser.importCoordinates: undefined molecule')
            return True
        #end if

        if nmodels == None:
            nmodels = self.modelCount # import all models found in pdfFile
        #end if

        if nmodels > self.modelCount:
            NTerror('pdbParser.importCoordinates: requesting %d models; only %d present', nmodels, self.modelCount)
            return True
        #end if

        model = self.molecule.modelCount # set current model from models already present
        foundModel = False
        for record in self.pdbRecords:
            recordName = record._name.strip()
            if recordName == "MODEL":
                foundModel = True
#                NTdebug('pdbParser.importCoordinates: importing as MODEL %d', model)
                continue

            elif recordName == "ENDMDL":
                model += 1
                if model == self.molecule.modelCount + nmodels:
                    break

            elif recordName == "ATOM" or recordName == "HETATM":
#                if (not record.atm.skip) and (record.atm.atom != None):
                if not record.atm:
                    continue   
#                NTdebug("record.atm: %s" % record.atm)             
                if record.atm.skip:
                    continue                
                if not record.atm.atom:
                    continue                
                atom = record.atm.atom
                # Check if the coordinate already exists for this model
                # This might happen when alternate locations are being
                # specified. Simplify to one coordinate per model.
                if len(atom.coordinates) <= model:
                    atom.addCoordinate(record.x, record.y, record.z, Bfac = record.tempFactor, occupancy = record.occupancy)
                else:
                    NTdebug('pdbParser.importCoordinates: Skipping duplicate coordinate within same record (%s)' % record)
                #end if
            #end if
        #end for
        if not foundModel: # X-rays do not have MODEL record
            self.molecule.modelCount += 1
        else:
            self.molecule.modelCount = model

        if update:
            self.molecule.updateAll()

        NTdebug('pdbParser.importCoordinates: %s', self.molecule)
        return False
    #end def
#end class

def PDB2Molecule(pdbFile, moleculeName, convention = IUPAC, nmodels = None)   :
    """Initialize  Molecule 'moleculeName' from pdbFile
       convention eq PDB, CYANA, CYANA2 or XPLOR, IUPAC
       optionally only include nmodels

       Return molecule instance or None on error
    """
#    showMaxNumberOfWarnings = 100 # was 100
#    shownWarnings = 0
#
#    if not os.path.exists(pdbFile):
#        NTerror('PDB2Molecule: missing PDB-file "%s"', pdbFile)
#        return None
#
#    NTdetail('==> Parsing pdbFile "%s" ... ', pdbFile )
#
#    pdb = PyMMLib.PDBFile( pdbFile )
#    mol = Molecule( name=moleculeName )
#
##    mol.pdb = pdb
#    mol.modelCount  = 0
#    foundModel = False
#
#    for record in pdb:
#        recordName = record._name.strip()
#        if  recordName == 'REMARK':
#            continue # JFD: this used to be a pass but that's weird.
#
#        if recordName == "MODEL":
#            foundModel = True
#            continue
#        if recordName == "ENDMDL":
#            mol.modelCount += 1
#            if nmodels and (mol.modelCount >= nmodels):
#                break
#            continue
#
#        if recordName == "ATOM" or recordName == "HETATM":
#            # Skip records with a
#            # see if we can find a definition for this residue, atom name in the database
#            a = record.name
#            a = a.strip() # this improved reading 1y4o
#            if convention == CYANA or convention == CYANA2:
#                # the residue names are in Cyana1.x convention (i.e. for GLU-)
#                # atm names of the Cyana1.x PDB files are in messed-up Cyana format
#                # So: 1HD2 becomes HD21 where needed:
#                a = moveFirstDigitToEnd(a)
#            # strip is already done in function
#            atm = NTdbGetAtom( record.resName, a, convention )
#
#
#            # JFD adds to just hack these debilitating simple variations.
#            if not atm: # some besides cyana have this too; just too easy to hack here
##                print "Atom ["+a+"] was mismatched at first"
#                a = moveFirstDigitToEnd(a)
#                atm = NTdbGetAtom( record.resName, a, convention )
#            if not atm:
#                if a == 'H': # happens for 1y4o_1model reading as cyana but in cyana we have hn for INTERNAL_0
#                    a = 'HN'
#                elif a == 'HN': # for future examples.
#                    a = 'H'
#                atm = NTdbGetAtom( record.resName, a, convention )
#            if not atm:
#                if shownWarnings <= showMaxNumberOfWarnings:
#                    NTwarning('PDB2Molecule: %s format, model %d incompatible record (%s)' % (
#                             convention, mol.modelCount+1, record))
#                    if shownWarnings == showMaxNumberOfWarnings:
#                        NTwarning('And so on.')
#                    shownWarnings += 1
#                continue
#            if atm.residueDef.hasProperties('cyanaPseudoResidue'):
#                # skip CYANA pseudo residues
#                continue
#
#            # we did find a match in the database
#            # Not all PDB files have chainID's !@%^&*
#            # They do; if none returned then take the space that is always present!
#            chainId = Chain.defaultChainId
#            if record.has_key('chainID'):
#                chainId = record.chainID.strip()
#                chainId = ensureValidChainId(chainId)
#
#            resID    = record.resSeq
#            resName  = atm.residueDef.name
#            fullName = resName+str(resID)
#            atmName  = atm.name
#
#            # check if this chain,fullName,atmName already exists in the molecule
#            # if not, add chain or residue
#            if not chainId in mol:
#                mol.addChain( chainId )
#            #end if
#
#            if not fullName in mol[chainId]:
#                res = mol[chainId].addResidue( resName, resID )
#                res.addAllAtoms()
#            #end if
#
#            atom = mol[chainId][fullName][atmName]
#
#            # Check if the coordinate already exists for this model
#            # This might happen when alternate locations are being
#            # specified. Simplify to one coordinate per model.
#            numCoorinates = len(atom.coordinates)
#            numModels     = mol.modelCount + 1 # current model counts already
#            if numCoorinates < numModels:
#                atom.addCoordinate( record.x, record.y, record.z, Bfac=record.tempFactor )
#            else:
#                NTwarning('Skipping duplicate coordinate within same record (%s)' % record)
#        #end if
#    #end for
#    if shownWarnings:
#        NTwarning('Total number of warnings: ' + `shownWarnings`)
#
#    # Patch to get modelCount right for X-ray structures with only one model
#    if not foundModel:
#        mol.modelCount += 1
#    NTdetail( '==> PDB2Molecule: new Molecule %s from %s', mol, pdbFile )
#    # delete the PyMMlib pdbFile instance # JFD: why?
#    del(pdb)
    parser = pdbParser(pdbFile, convention = convention)
    if not parser:
        return None
    mol = parser.initMolecule(moleculeName)
    if not mol:
        return None
    parser.importCoordinates(nmodels = nmodels)
    return mol
#end def
# Add as a staticmethod to Molecule class
Molecule.PDB2Molecule = staticmethod(PDB2Molecule)


def moleculeToPDBfile(molecule, path, model = None, convention = IUPAC, max_models = None):
    """
    Save a molecule instance to PDB file.
    Convention eq PDB, CYANA, CYANA2, XPLOR.

    For speedup reasons, this routine should be explicitly coded.
    This routine should eventually replace toPDB.

    NB model should be ZERO for the first model. Not one.
    Returns True on error.
    """
    NTdebug('MoleculeToPDBfile: %s, path=%s, model=%s, convention=%s',
             molecule, path, model, convention)
    pdbFile = molecule.toPDB(model = model, convention = convention, max_models = None)
    if not pdbFile:
        return True
    pdbFile.save(path)
    del(pdbFile)
#end def
Molecule.toPDBfile = moleculeToPDBfile

def initPDB(project, pdbFile, convention = IUPAC, name = None, nmodels = None, update = True, allowNonStandardResidue = True):
    """Initialize Molecule from pdbFile.
       convention eq. CYANA, CYANA2, XPLOR, IUPAC

       Optionally include only nmodels.
       Optionally do not update dihedrals, mean-coordiates, .. (Be careful; only intended for conversion
       purposes).

       returns molecule instance or None on error
    """
    if not os.path.exists(pdbFile):
        NTerror('Project.initPDB: missing PDB-file "%s"', pdbFile)

#    NTmessage('==> initializing from PDB file "%s"', pdbFile) # repeated in the parser.

    if not name:
        _path, name, _ext = NTpath(pdbFile)
#    molecule = PDB2Molecule( pdbFile, name, convention = convention, nmodels=nmodels)
    parser = pdbParser(pdbFile, convention = convention, allowNonStandardResidue = allowNonStandardResidue)
    if not parser:
        return None
    molecule = parser.initMolecule(name)
    if not molecule:
        return None
    if not molecule:
        NTerror('Project.initPDB: failed parsing PDB-file "%s"', pdbFile)
        return None
    parser.importCoordinates(nmodels = nmodels, update = update)
    project.appendMolecule(molecule)
#    if update:
#        project.molecule.updateAll()
    #end if
    project.addHistory(sprintf('New molecule from PDB-file "%s"', pdbFile))
    project.updateProject()
    return molecule
#end def


def importPDB(project, pdbFile, convention = IUPAC, nmodels = None):
    """Import coordinates from pdbFile
        return pdbFile or None on error
    """
    if not project.molecule:
        NTerror("importPDB: no molecule defined")
        return None
    if not importFromPDB(project.molecule, pdbFile, convention, nmodels = nmodels):
        return None

    project.addHistory(sprintf('importPDB from "%s"', pdbFile))
    project.updateProject()
    NTmessage('%s', project.molecule.format())
    #end if
    return pdbFile
#end def

def export2PDB(project, tmp = None):
    """Export coordinates to pdb file
    """
    for mol in project.molecules:
        if mol.modelCount > 0:
            fname = project.path(project.directories.PDB, mol.name + '.pdb')
            NTdetail('==> Exporting to PDB file "%s"', fname)
            pdbFile = mol.toPDB(convention = IUPAC)
            pdbFile.save(fname)
            del(pdbFile)
        #end if
    #end for
#end def

# register the functions
methods = [(initPDB, None),
            (importPDB, None)
           ]
#saves    = []
#restores = []
exports = [(export2PDB, None)
           ]