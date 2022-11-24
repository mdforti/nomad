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
import PropTypes from 'prop-types'
import { PropertyGrid, PropertyItem } from '../entry/properties/PropertyCard'
import SolarCell from './SolarCell'
import BandGap from './BandGap'

// Displays the set of optoelectronic properties.
const OptoelectronicProperties = React.memo(({
  bandGap,
  solarCell
}) => {
  return <PropertyGrid>
    <PropertyItem title="Solar cell" xs={12} height="auto" minHeight="100px">
      <SolarCell data={solarCell} />
    </PropertyItem>
    <PropertyItem title="Band gap" xs={12} height="auto" minHeight="100px">
      <BandGap
        section="results.properties.optoelectronic.band_gap_optical"
        data={bandGap}
      />
    </PropertyItem>
  </PropertyGrid>
})

OptoelectronicProperties.propTypes = {
  bandGap: PropTypes.any, // Set to false if not available, set to other falsy value to show placeholder.
  solarCell: PropTypes.any // Set to false if not available, set to other falsy value to show placeholder.
}

export default OptoelectronicProperties
