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
import React, {useCallback} from 'react'
import {MenuItem} from '@material-ui/core'
import PropTypes from 'prop-types'
import {getFieldProps, TextFieldWithHelp} from './StringEditQuantity'

export const EnumEditQuantity = React.memo((props) => {
  const {quantityDef, section, onChange, ...otherProps} = props

  const handleChange = useCallback((value) => {
    if (onChange) {
      onChange(value === '' ? undefined : value, section, quantityDef)
    }
  }, [onChange, quantityDef, section])

  return <TextFieldWithHelp
    select variant='filled' size='small' withOtherAdornment fullWidth
    defaultValue={section[quantityDef.name] || quantityDef.default || ''}
    onChange={event => handleChange(event.target.value)}
    {...getFieldProps(quantityDef)}
    {...otherProps}
  >
    {quantityDef.type?.type_data.map(item => <MenuItem value={item} key={item}>{item}</MenuItem>)}
  </TextFieldWithHelp>
})
EnumEditQuantity.propTypes = {
  quantityDef: PropTypes.object.isRequired,
  section: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired
}
