import numpy as np
from elasticsearch_dsl import InnerDoc
from nomad.metainfo import MSection, Section, SubSection, Quantity, MEnum, units


class Material(MSection):
    m_def = Section(
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc),
        description="""
        Section for storing the data that links this entry into a specific material.
        """
    )

    # Material-specific
    system_type = Quantity(
        type=MEnum(bulk="bulk", two_d="2D", one_d="1D", unavailable="unavailable"),
        description="""
        "Character of physical system's geometry, e.g. bulk, surface... ",
        """
    )
    material_hash = Quantity(
        type=str,
        description="""
        A fixed length, unique material identifier in the form of a hash
        digest.
        """
    )
    number_of_atoms = Quantity(
        type=int,
        description="""
        Number of atoms in the bravais cell."
        """
    )
    bravais_lattice = Quantity(
        type=MEnum("aP", "mP", "mS", "oP", "oS", "oI", "oF", "tP", "tI", "hR", "hP", "cP", "cI", "cF"),
        description="""
        The Bravais lattice type in the Pearson notation, where the first
        lowercase letter indicates the crystal system, and the second uppercase
        letter indicates the lattice type. The value can only be one of the 14
        different Bravais lattices in three dimensions.

        Crystal system letters:

        a = Triclinic
        m = Monoclinic
        o = Orthorhombic
        t = Tetragonal
        h = Hexagonal and Trigonal
        c = Cubic

        Lattice type letters:

        P = Primitive
        S (A, B, C) = One side/face centred
        I = Body centered
        R = Rhombohedral centring
        F = All faces centred
        """
    )
    crystal_system = Quantity(
        type=MEnum("triclinic", "monoclinic", "orthorhombic", "tetragonal", "trigonal", "hexagonal", "cubic"),
        description="""
        The detected crystal system. One of seven possibilities in three dimensions.
        """
    )
    formula = Quantity(
        type=str,
        description="""
        Formula giving the composition and occurrences of the elements in the
        Hill notation for the irreducible unit cell.
        """
    )
    formula_reduced = Quantity(
        type=str,
        description="""
        Formula giving the composition and occurrences of the elements in the
        Hill notation for the irreducible unit cell. In this reduced form the
        number of occurences have been divided by the greatest common divisor.
        """
    )
    has_free_wyckoff_parameters = Quantity(
        type=bool,
        description="""
        Whether the material has any Wyckoff sites with free parameters. If a
        materials has free Wyckoff parameters, at least some of the atoms are
        not bound to a particular location in the structure but are allowed to
        move with possible restrictions set by the symmetry.
        """
    )
    material_classification = Quantity(
        type=str,
        description="""
        Contains the compound class and classification of the material
        according to springer materials in JSON format.
        """
    )
    material_name = Quantity(
        type=str,
        description="""
        Most meaningful name for a material.
        """
    )
    periodicity = Quantity(
        type=np.dtype('i1'),
        shape=["1..*"],
        description="""
        The indices of the periodic dimensions.
        """
    )
    point_group = Quantity(
        type=MEnum("1", "-1", "2", "m", "2/m", "222", "mm2", "mmm", "4", "-4", "4/m", "422", "4mm", "-42m", "4/mmm", "3", "-3", "32", "3m", "-3m", "6", "-6", "6/m", "622", "6mm", "-6m2", "6/mmm", "23", "m-3", "432", "-43m", "m-3m"),
        description="""
        Point group in Hermann-Mauguin notation, part of crystal structure
        classification. There are 32 point groups in three dimensional space.
        """
    )
    space_group_number = Quantity(
        type=int,
        description="""
        Integer representation of the space group, part of crystal structure classification, part of material definition.
        """
    )
    space_group_international_short_symbol = Quantity(
        type=str,
        description="""
        International short symbol notation of the space group.
        """
    )
    structure_prototype = Quantity(
        type=str,
        description="""
        The prototypical material for this crystal structure.
        """
    )
    structure_type = Quantity(
        type=str,
        description="""
        Classification according to known structure type, considering the point
        group of the crystal and the occupations with different atom types.
        """
    )
    strukturbericht_designation = Quantity(
        type=str,
        description="""
        Classification of the material according to the historically grown "strukturbericht".
        """
    )

    # Calculation-specific
    atom_labels = Quantity(
        type=str,
        shape=['1..*'],
        description="""
        Type (element, species) of each atom,
        """
    )
    atom_positions = Quantity(
        type=np.dtype('f8'),
        shape=['number_of_atoms', 3],
        description="""
        Position of each atom, given in relative coordinates.
        """
    )
    cell_normalized = Quantity(
        type=np.dtype('f8'),
        shape=[3, 3],
        description="""
        Unit cell in normalized form, meaning the bravais cell. This cell is
        representative and is idealized to match the detected symmetry
        properties.
        """
    )
    cell_primitive = Quantity(
        type=np.dtype('f8'),
        shape=[3, 3],
        description="""
        Definition of the primitive unit cell in a form to be visualized well
        within the normalized cell. This cell is representative and is
        idealized to match the detected symmemtry properties.
        """
    )
    wyckoff_groups = Quantity(
        type=str,
        description="""
        Returns a list of information about the Wyckoff groups in the JSON format.

        An example of the output:
            [
                {
                    'wyckoff_letter': 'a',
                    'variables': {'z': 0.0},
                    'indices': [0, 6, 12],
                    'element': 'Bi'
                },
                {
                    'wyckoff_letter': 'b',
                    'variables': {'x': 0.50155295, 'z': 0.87461175999999996},
                    'indices': [1, 3, 4, 7, 9, 10, 13, 15, 16],
                    'element': 'Ga'
                }, ...
            ]
        """
    )
    cell_angles_string = Quantity(
        type=str,
        description="""
        A summary of the cell angles, part of material definition.
        """
    )
    cell_volume = Quantity(
        type=float,
        description="""
        Cell volume for a specific calculation. The cell volume can only be
        reported consistently after normalization. Thus it corresponds to the
        normalized cell that is idealized to fit the detected symmetry and may
        not perfectly correspond to the original simulation cell.
        """
    )
    lattice_parameters = Quantity(
        type=np.dtype('f8'),
        shape=[6],
        description="""
        Lattice parameters of a specific calculation. The lattice parameters
        can only be reported consistently after normalization. Thus they
        correspond to the normalized cell that is idealized to fit the detected
        symmetry and may not perfectly correspond to the original simulation
        cell.
        """
    )


class Method(MSection):
    m_def = Section(
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc),
        description="""
        Section for storing Encyclopedia-specific method information.
        """
    )
    method_type = Quantity(
        type=str,
        description="""
        Generic name for the used methodology.
        """
    )
    basis_set_type = Quantity(
        type=MEnum("Numeric AOs", "Gaussians", "(L)APW+lo", "FLAPW (full-potential linearized augmented planewave)", "Plane waves", "Real-space grid", "Local-orbital minimum-basis"),
        description="""
        Basic type of the used basis set.
        """
    )
    code_name = Quantity(
        type=str,
        description="""
        Name of the code used to perform the calculation.
        """
    )
    code_version = Quantity(
        type=str,
        description="""
        Version of the code used for the calculation.
        """
    )
    core_electron_treatment = Quantity(
        type=MEnum("full all electron", "all electron frozen core", "pseudopotential", "unavailable"),
        description="""
        How the core electrons are described.
        """
    )
    functional_long_name = Quantity(
        type=str,
        description="""
        Full identified for the used exchange-correlation functional.
        """
    )
    functional_type = Quantity(
        type=str,
        description="""
        Basic type of the used exchange-correlation functional.
        """
    )
    method_hash = Quantity(
        type=str,
        description="""
        A fixed length, unique method identifier in the form of a hash
        digest.
        """
    )
    group_eos_hash = Quantity(
        type=str,
        description="""
        A fixed length, unique identifier for equation-of-state calculations.
        Only calculations wihtin the same upload will be grouped under the same
        hash.
        """
    )
    group_parametervariation_hash = Quantity(
        type=str,
        description="""
        A fixed length, unique identifier for calculations where structure is
        identical but the used computational parameters are varied.  Only
        calculations within the same upload will be grouped under the same
        hash.
        """
    )
    gw_starting_point = Quantity(
        type=str,
        description="""
        The exchange-correlation functional that was used as a starting point for this GW calculation.
        """
    )
    gw_type = Quantity(
        type=MEnum("G0W0", "scGW"),
        description="""
        Basic type of GW calculation.
        """
    )
    settings_basis_set = Quantity(
        type=str,
        description="""
        Basis set settings in JSON format.
        """
    )
    smearing_kind = Quantity(
        type=MEnum("gaussian", "fermi", "marzari-vanderbilt", "methfessel-paxton", "tetrahedra"),
        description="""
        Smearing function used for the electronic structure calculation.
        """
    )
    smearing_parameter = Quantity(
        type=float,
        description="""
        Parameter for smearing, usually the width.
        """
    )


class RunType(MSection):
    m_def = Section(
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc),
        description="""
        Section for storing Encyclopedia-specific run type information.
        """
    )
    run_type = Quantity(
        type=MEnum(
            single_point="single point",
            geometry_optimization="geometry optimization",
            molecular_dynamics="molecular dynamics",
            phonon_calculation="phonon calculation",
            elastic_constants="elastic constants",
            qha_calculation="QHA calculation",
            gw_calculation="GW calculation",
            equation_of_state="equation of state",
            parameter_variation="parameter variation",
            unavailable="unavailable"),
        description="""
        Defines the type of run identified for this entry.
        """
    )


class Properties(MSection):
    m_def = Section(
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc),
        description="""
        Section for storing Encyclopedia-specific properties.
        """
    )
    atomic_density = Quantity(
        type=float,
        unit=units.m**(-3),
        description="""
        Atomic density of the material (atoms/volume)."
        """
    )
    mass_density = Quantity(
        type=float,
        unit=units.kg / units.m**3,
        description="""
        Mass density of the material based on the structural information.
        """
    )


class Encyclopedia(MSection):
    m_def = Section(
        name="encyclopedia",
        a_flask=dict(skip_none=True),
        a_elastic=dict(type=InnerDoc)
    )
    mainfile_uri = Quantity(
        type=str,
        description="""
        Path of the main file.
        """
    )
    material = SubSection(sub_section=Material.m_def, repeats=False)
    method = SubSection(sub_section=Method.m_def, repeats=False)
    properties = SubSection(sub_section=Properties.m_def, repeats=False)
    run_type = SubSection(sub_section=RunType.m_def, repeats=False)
