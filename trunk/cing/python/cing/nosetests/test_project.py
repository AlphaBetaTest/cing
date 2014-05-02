from nose import with_setup
import os

import cing
from cing import definitions as cdefs
from cing import constants
from cing.core import classes
from cing.core import molecule
from cing.Libs import io
from cing.core import validation

project = None

TEST = 'test'

def setup_DummyProject():
    global project
    os.chdir(cdefs.cingDefinitions.tmpdir)
    print('Now in %s' % cdefs.cingDefinitions.tmpdir)
    project = cing.openProject(TEST, constants.PROJECT_NEW)
    # create a molecule
    mol = molecule.Molecule(TEST)
    project.appendMolecule(mol)
    c = mol.addChain('A')
    c.addResidue('ALA', 1, Nterminal = True)
    c.addResidue('VAL', 2)
    c.addResidue('PHE', 3)
    c.addResidue('ARG', 4)
    c.addResidue('GLU', 5, Cterminal = True)
    c = mol.addChain('B')
    c.addResidue('DG', 1, Nterminal = True)
    c.addResidue('DA', 2)
    c.addResidue('DT', 3)
    c.addResidue('DC', 4, Cterminal = True)
    c = mol.addChain('C')
    c.addResidue('RGUA', 1, convention=constants.INTERNAL_0, Nterminal = True)
    c.addResidue('RADE', 2, convention=constants.INTERNAL_0)
    c.addResidue('URA', 3, convention=constants.INTERNAL_0) # not RTHY normally of course.
    c.addResidue('RTHY', 4, convention=constants.INTERNAL_0)
    c.addResidue('RCYT',  5, convention=constants.INTERNAL_0, Cterminal = True)
    c = mol.addChain('D')
    for i in range(1,11):
        c.addResidue('HOH', i )
    # end for
    c = mol.addChain('E') # Unknown residue to CING
    c.addResidue('ACE', 1)
    c = mol.addChain('F') # Ions are also other
    c.addResidue('CA2P', 1)
    for residue in mol.allResidues():
        residue.addAllAtoms()
    # end for
    mol.updateAll()
    io.message('{0}\n',mol.format())


def teardown_project():
    global project
    if project is not None:
        project.close(save=False)


def test_projectNotPresent():
    print('Forced error:')
    project = classes.Project.open('notPresent','old')
    assert project is None


def test_rootPath():
    root,name,ext = classes.Project.rootPath('test')
    assert root == 'test.cing'
    assert name == 'test'
    root,name,ext = classes.Project.rootPath('test.cing')
    assert root == 'test.cing'
    assert name == 'test'
    root,name,ext = classes.Project.rootPath('test.cing/project.sml')
    assert root == 'test.cing'
    assert name == 'test'
    assert ext == '.sml'
    root,name, ext = classes.Project.rootPath('test.tgz')
    assert root == 'test.cing'
    assert name == 'test'
    assert ext == '.tgz'


@with_setup(setup_DummyProject,teardown_project)
def test_openSaveProject():
    assert project is not None
    project.created = io.Time(10.0) # silly date
    # this will test the save routines
    assert project.save() == False
    # this will test the restore routines
    p = project.open(TEST,constants.PROJECT_OLD)
    assert p is not None
    assert p.created == 10.0


@with_setup(setup_DummyProject,teardown_project)
def test_pluginRoutines():
    assert project is not None
    pdefs = project.getStatusDict(TEST)
    assert pdefs is not None

    vobj = validation.ValidationResult()
    vobj.value = 10
    validation.setValidationResult(project.molecule,TEST,vobj)
    pdefs.present = True
    result = project._savePluginData(TEST, saved=True)
    assert result == False

    result = project._restorePluginData(TEST)
    assert result == False
    vobj = validation.getValidationResult(project.molecule,TEST)
    assert vobj is not None
    assert vobj.value == 10

