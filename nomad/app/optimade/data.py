from ase.data import chemical_symbols
from elasticsearch_dsl import Keyword, Integer, Float, Text, InnerDoc, Nested

from nomad.metainfo import MObject, Section, Quantity, Enum, Units


class ElementRatio(InnerDoc):
    element = Keyword()
    ratio = Float()

    @staticmethod
    def from_structure_entry(entry: 'StructureEntry'):
        return [
            ElementRatio(element=entry.elements[i], ratio=entry.elements_ratios[i])
            for i in range(0, entry.nelements)]


class Optimade():
    def __init__(self, query: bool = False, entry: bool = False):
        pass


class StructureEntry(MObject):
    m_section = Section(
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2'],
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc))

    elements = Quantity(
        type=Enum(chemical_symbols), shape=['1..*'],
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.1'],
        a_elastic=dict(type=Keyword),
        a_optimade=Optimade(query=True, entry=True))
    """ Names of the different elements present in the structure. """

    nelements = Quantity(
        type=int,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.2'],
        a_elastic=dict(type=Integer),
        a_optimade=Optimade(query=True, entry=True))
    """ Number of different elements in the structure as an integer. """

    elements_ratios = Quantity(
        type=float, shape=['nelements'],
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.3'],
        a_elastic=dict(type=lambda: Nested(ElementRatio), mapping=ElementRatio.from_structure_entry),
        a_optimade=Optimade(query=True, entry=True))
    """ Relative proportions of different elements in the structure. """

    chemical_formula_descriptive = Quantity(
        type=str,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.4'],
        a_elastic=dict(type=Text, other_types=dict(keyword=Keyword)),
        a_optimade=Optimade(query=True, entry=True))
    """
    The chemical formula for a structure as a string in a form chosen by the API
    implementation.
    """

    chemical_formula_reduced = Quantity(
        type=str,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.5'],
        a_elastic=dict(type=Text, other_types=dict(keyword=Keyword)),
        a_optimade=Optimade(query=True, entry=True))
    """
    The reduced chemical formula for a structure as a string with element symbols and
    integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.
    """

    chemical_formula_hill = Quantity(
        type=str,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.6'],
        a_elastic=dict(type=Text, other_types=dict(keyword=Keyword)),
        a_optimade=Optimade(query=True, entry=False))
    """
    The chemical formula for a structure in Hill form with element symbols followed by
    integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.
    """

    chemical_formula_anonymous = Quantity(
        type=str,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.7'],
        a_elastic=dict(type=Text, other_types=dict(keyword=Keyword)),
        a_optimade=Optimade(query=True, entry=True))
    """
    The anonymous formula is the chemical_formula_reduced, but where the elements are
    instead first ordered by their chemical proportion number, and then, in order left to
    right, replaced by anonymous symbols A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and
    so on.
    """

    dimension_types = Quantity(
        type=int, shape=[3],
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.8'],
        a_elastic=dict(type=Integer, mapping=lambda a: sum(a.dimension_types)),
        a_optimade=Optimade(query=True, entry=True))
    """
    List of three integers. For each of the three directions indicated by the three lattice
    vectors (see property lattice_vectors). This list indicates if the direction is
    periodic (value 1) or non-periodic (value 0). Note: the elements in this list each
    refer to the direction of the corresponding entry in lattice_vectors and not
    the Cartesian x, y, z directions.
    """

    lattice_vectors = Quantity(
        type=float, shape=[3, 3], unit=Units.Angstrom,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.9'],
        a_optimade=Optimade(query=False, entry=True))
    """ The three lattice vectors in Cartesian coordinates, in ångström (Å). """

    cartesian_site_positions = Quantity(
        type=float, shape=['nsites', 3], unit=Units.Angstrom,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.10'],
        a_optimade=Optimade(query=False, entry=True))
    """
    Cartesian positions of each site. A site is an atom, a site potentially occupied by
    an atom, or a placeholder for a virtual mixture of atoms (e.g., in a virtual crystal
    approximation).
    """

    nsites = Quantity(
        type=int,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.11'],
        a_elastic=dict(type=Integer),
        a_optimade=Optimade(query=True, entry=True))
    """ An integer specifying the length of the cartesian_site_positions property. """

    species_at_sites = Quantity(
        type=str, shape=['nsites'],
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.12'],
        a_optimade=Optimade(query=False, entry=True))
    """
    Name of the species at each site (where values for sites are specified with the same
    order of the cartesian_site_positions property). The properties of the species are
    found in the species property.
    """

    # TODO assemblies

    structure_features = Quantity(
        type=Enum(['disorder', 'unknown_positions', 'assemblies']), shape=['1..*'],
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.15'],
        a_elastic=dict(type=Keyword),
        a_optimade=Optimade(query=True, entry=True))
    """
    A list of strings that flag which special features are used by the structure.

    - disorder: This flag MUST be present if any one entry in the species list has a
      chemical_symbols list that is longer than 1 element.
    - unknown_positions: This flag MUST be present if at least one component of the
      cartesian_site_positions list of lists has value null.
    - assemblies: This flag MUST be present if the assemblies list is present.
    """


class Species(MObject):
    """
    Used to describe the species of the sites of this structure. Species can be pure
    chemical elements, or virtual-crystal atoms representing a statistical occupation of a
    given site by multiple chemical elements.
    """

    m_section = Section(
        repeats=True, parent=StructureEntry.m_section,
        links=['https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md#h.6.2.13'])

    name = Quantity(
        type=str,
        a_optimade=Optimade(entry=True))
    """ The name of the species; the name value MUST be unique in the species list. """

    chemical_symbols = Quantity(
        type=Enum(chemical_symbols + ['x', 'vacancy']), shape=['1..*'],
        a_optimade=Optimade(entry=True))
    """
    A list of strings of all chemical elements composing this species.

    It MUST be one of the following:

    - a valid chemical-element name, or
    - the special value "X" to represent a non-chemical element, or
    - the special value "vacancy" to represent that this site has a non-zero probability
      of having a vacancy (the respective probability is indicated in the concentration
      list, see below).

    If any one entry in the species list has a chemical_symbols list that is longer than 1
    element, the correct flag MUST be set in the list structure_features (see
    structure_features)
    """

    concentration = Quantity(
        type=float, shape=['1..*'],
        a_optimade=Optimade(entry=True))
    """
    A list of floats, with same length as chemical_symbols. The numbers represent the
    relative concentration of the corresponding chemical symbol in this species. The
    numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall
    only in the following two categories:

    - Numerical errors when representing float numbers in fixed precision, e.g. for two
      chemical symbols with concentrations 1/3 and 2/3, the concentration might look
      something like [0.33333333333, 0.66666666666]. If the client is aware that the sum
      is not one because of numerical precision, it can renormalize the values so that the
      sum is exactly one.
    - Experimental errors in the data present in the database. In this case, it is the
      responsibility of the client to decide how to process the data.

    Note that concentrations are uncorrelated between different sites (even of the same
    species).
    """

    mass = Quantity(type=float, unit=Units.amu, a_optimade=dict(entry='optional'))

    original_name = Quantity(type=str, a_optimade=dict(entry='optional'))
    """
    Can be any valid Unicode string, and SHOULD contain (if specified) the name of the
    species that is used internally in the source database.

    Note: With regards to "source database", we refer to the immediate source being
    queried via the OPTiMaDe API implementation. The main use of this field is for source
    databases that use species names, containing characters that are not allowed (see
    description of the species_at_sites list).
    """
