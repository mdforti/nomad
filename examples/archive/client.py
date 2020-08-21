'''
A simple example that uses the NOMAD client library to access the archive.
'''

from nomad.client import ArchiveQuery
from nomad.metainfo import units


query = ArchiveQuery(
    query={
        'dft.compound_type': 'binary',
        'dft.crystal_system': 'cubic',
        'dft.code_name': 'FHI-aims',
        'atoms': ['O']
    },
    required={
        'section_run[0]': {
            'section_single_configuration_calculation[-2]': {
                'energy_total': '*'
            },
            'section_system[-2]': '*'
        }
    },
    parallel=5,
    per_page=20,
    max=1000)

print(query)

for result in query[0:100]:
    run = result.section_run[0]
    energy = run.section_single_configuration_calculation[0].energy_total
    formula = run.section_system[0].chemical_composition_reduced
    print('%s: energy %s' % (formula, energy.to(units.hartree)))
