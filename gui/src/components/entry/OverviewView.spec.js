/*
 * Copyright The NOMAD Authors.
 *
 * This file is part of NOMAD. See https://nomad-lab.eu for further info.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from 'react'
import 'regenerator-runtime/runtime'
import { waitFor, within } from '@testing-library/dom'
import { render, screen, expectQuantity, readArchive, startAPI, closeAPI } from '../conftest'
import { expectPlotButtons } from '../visualization/conftest'
import {
  expectComposition,
  expectSymmetry,
  expectLatticeParameters
} from './conftest'
import OverviewView from './OverviewView'
import EntryContext from './EntryContext'

beforeAll(() => {
  startAPI('tests.states.entry.dft', 'tests/data/entry/dft')
})

afterAll(() => {
  closeAPI()
})

test('correctly renders metadata and all properties', async () => {
  render(<EntryContext entryId={'dft_bulk'}>
    <OverviewView />
  </EntryContext>)

  // Wait to load the entry metadata, i.e. wait for some of the text to appear
  await screen.findByText('VASP')

  // We read the JSON archive corresponding to the tested API entry. Using this
  // data makes writing assertions much easier.
  const index = (await readArchive('../../../tests/states/archives/dft.json'))[1]

  // Check if all method quantities are shown (on the left)
  expectQuantity('results.method.simulation.program_name', 'VASP')
  expectQuantity('results.method.simulation.program_version', '1')
  expectQuantity('results.method.simulation.dft.xc_functional_type', 'GGA')
  expectQuantity('results.method.simulation.dft.xc_functional_names', 'GGA_C_PBE, GGA_X_PBE')
  expectQuantity('results.method.simulation.dft.basis_set_type', 'plane waves')
  expectQuantity('results.method.simulation.dft.basis_set_name', 'STO-3G')
  expectQuantity('results.method.simulation.dft.van_der_Waals_method', 'G06')
  expectQuantity('results.method.simulation.dft.relativity_method', 'scalar_relativistic_atomic_ZORA')

  // Check if all metadata is shown (on the left)
  expectQuantity('results.method.method_name', index)
  expectQuantity('comment', index)
  expectQuantity('references', index.references[0])
  expectQuantity('authors', 'Markus Scheidgen')
  expectQuantity('mainfile', index)
  expectQuantity('entry_id', index)
  expectQuantity('upload_id', index)
  expectQuantity('results.material.material_id', index)
  expectQuantity(undefined, `${index.nomad_version}/${index.nomad_commit}`, 'processing version', 'Version used in the last processing')
  // TODO: add the following to the state for testing.
  // expectQuantity('datasets', index.datasets[0].dataset_name)
  // expectQuantity('upload_create_time', new Date(index.upload_create_time).toLocaleString())
  // expectQuantity('last_processing_time', new Date(index.last_processing_time).toLocaleString())

  // Check if all material data is shown (on the right, in the materials card)
  expectComposition(index)
  expectSymmetry(index)
  expectLatticeParameters(index)
  // expectStructure(index) // TODO: The click introduced here breaks the subsequent tests

  // Check if all the property cards are shown
  expect(screen.getByText('Electronic properties')).toBeInTheDocument()
  expect(screen.getByText('Band structure')).toBeInTheDocument()
  expect(screen.getByText('Density of states')).toBeInTheDocument()
  expect(screen.getByText('Brillouin zone')).toBeInTheDocument()

  expect(screen.getByText('Vibrational properties')).toBeInTheDocument()
  expect(screen.getByText('Phonon dispersion')).toBeInTheDocument()
  expect(screen.getByText('Phonon density of states')).toBeInTheDocument()
  expect(screen.getByText('Heat capacity')).toBeInTheDocument()
  expect(screen.getByText('Helmholtz free energy')).toBeInTheDocument()
  expect(screen.getByText('Mechanical properties')).toBeInTheDocument()
  expect(screen.getByText('Energy-volume curve')).toBeInTheDocument()
  expect(screen.getByText('Bulk modulus')).toBeInTheDocument()
  expect(screen.getByText('Shear modulus')).toBeInTheDocument()

  // Check if all placeholders disappear
  const dosPhononPlaceholder = screen.queryByTestId('dos-phonon-placeholder')
  const bsPhononPlaceholder = screen.queryByTestId('bs-phonon-placeholder')
  const heatCapacityPlaceholder = screen.queryByTestId('heat-capacity-placeholder')
  const energyFreePlaceholder = screen.queryByTestId('energy-free-placeholder')
  const dosElectronicPlaceholder = screen.queryByTestId('dos-electronic-placeholder')
  const bsElectronicPlaceholder = screen.queryByTestId('bs-electronic-placeholder')
  const energyVolumeCurvePlaceholder = screen.queryByTestId('energy-volume-curve-placeholder')
  await waitFor(() => { expect(dosElectronicPlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(bsElectronicPlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(dosPhononPlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(bsPhononPlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(heatCapacityPlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(energyFreePlaceholder).not.toBeInTheDocument() })
  await waitFor(() => { expect(energyVolumeCurvePlaceholder).not.toBeInTheDocument() })

  // The test DOM does not support canvas or WebGL, and trying to add mocks for
  // them does not seem to work ATM. Thus we expect a message saying that the
  // 3D viewers are disabled.
  const msgs = screen.getAllByText('Could not display the visualization as your browser does not support WebGL content.')
  expect(msgs).toHaveLength(2)

  // Check that plot buttons are displayed
  const dosElectronic = screen.getByTestId('dos-electronic')
  expectPlotButtons(dosElectronic)
  const bsElectronic = screen.getByTestId('bs-electronic')
  expectPlotButtons(bsElectronic)
  const bsPhonon = screen.getByTestId('bs-phonon')
  expectPlotButtons(bsPhonon)
  const dosPhonon = screen.getByTestId('dos-phonon')
  expectPlotButtons(dosPhonon)
  const heatCapacity = screen.getByTestId('heat-capacity')
  expectPlotButtons(heatCapacity)
  const energyFree = screen.getByTestId('energy-free')
  expectPlotButtons(energyFree)
  const energyVolumeCurve = screen.getByTestId('energy-volume-curve')
  expectPlotButtons(energyVolumeCurve)

  // Check that tables are shown
  const bulkModulus = screen.getByTestId('bulk-modulus')
  expect(within(bulkModulus).getByText('Type')).toBeInTheDocument()
  expect(within(bulkModulus).getByText('Value (GPa)')).toBeInTheDocument()
  expect(within(bulkModulus).getByText('murnaghan')).toBeInTheDocument()
  const shearModulus = screen.getByTestId('shear-modulus')
  expect(within(shearModulus).getByText('Type')).toBeInTheDocument()
  expect(within(shearModulus).getByText('Value (GPa)')).toBeInTheDocument()
  expect(within(shearModulus).getByText('voigt_reuss_hill_average')).toBeInTheDocument()
})