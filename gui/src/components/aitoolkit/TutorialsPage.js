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
import React, { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Grid,
  TextField,
  Typography,
  Divider,
  IconButton,
  makeStyles
} from '@material-ui/core'
import { Link } from 'react-router-dom'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { StringParam, useQueryParams } from 'use-query-params'
import TutorialsIcon from '../../images/AIT_ico_bp_tutorial.svg'
import ArrowIcon from '../../images/AIT_ico_bd_link_go_to.svg'
import ReproduceIcon from '../../images/AIT_ico_bb_replicate.svg'
import AccordionsList from './AccordionsList'
import FigureAI from '../../images/AIT_illu_AIT.svg'
import tutorials from '../../toolkitMetadata'

export const useStyles = makeStyles(theme => ({
  root: {
    margin: theme.spacing(3),
    width: '100%',
    marginLeft: 'auto',
    marginRight: 'auto',
    maxWidth: '1052px',
    marginBottom: '150px'
  },
  sectionIcon: {
    marginTop: theme.spacing(3)
  },
  sectionTitle: {
    marginBottom: theme.spacing(1),
    marginLeft: theme.spacing(2),
    marginTop: '105px'
  },
  title: {
    color: '#2A3C67',
    fontSize: '35px',
    marginLeft: '-10px',
    fontWeight: theme.typography.fontWeightMedium,
    marginTop: '-70px'
  },
  deck: {
    color: '#2A3C67',
    fontSize: '22px',
    marginTop: '20px',
    lineHeight: '30px',
    marginLeft: '-10px',
    width: '518px'
  },
  icon: {
    height: '371px',
    marginTop: '-20px',
    marginLeft: '100px'
  },
  filter: {
    fontWeight: theme.typography.fontWeightMedium,
    color: '#2A3C67',
    fontSize: '20px',
    marginTop: '60px',
    marginLeft: '0px'
  },
  autocomplete: {
    height: 'auto',
    color: '#2A3C67',
    border: '3px solid rgba(127, 239, 239, 1)',
    borderRadius: '10px 10px 10px 10px',
    marginTop: '10px',
    marginLeft: '0px',
    width: '240px'
  },
  tutorialsList: {
    marginTop: '50px'
  },
  fieldText: {
    color: '#2A3C67',
    fontWeight: theme.typography.fontWeightMedium
  },
  textLevel: {
    textAlign: 'left',
    color: '#2A3C67',
    fontSize: '22px',
    height: '22px',
    marginTop: '-16px'
  },
  tutorialsDivider: {
    backgroundColor: 'rgba(127, 239, 239, 1)',
    height: '13px',
    borderRadius: '4px'
  },
  titleSecondary: {
    fontWeight: 'bold',
    color: 'rgba(127, 239, 239, 1)',
    fontSize: '35px',
    marginLeft: '-10px'
  },
  bottomButton: {
    color: '#F3F2F5',
    backgroundColor: '#F3F2F5',
    borderRadius: '30px',
    width: '242px',
    height: '70px',
    textAlign: 'center',
    align: 'center',
    marginTop: '40px',
    textTransform: 'none',
    fontSize: '12pt',
    lineHeight: '20px'
  },
  bottomIcon: {
    height: '300px',
    marginTop: '80px',
    marginLeft: '120px'
  }
}))

export default function TutorialsPage() {
  const styles = useStyles()
  const [queryParameters, setQueryParameters] = useQueryParams({
    author: StringParam, keyword: StringParam, method: StringParam, filterString: StringParam
  })
  const emptyQuery = {
    author: null,
    keyword: null,
    method: null,
    filterString: null
  }

  const filter = tutorial => {
    const {author, keyword, method} = queryParameters
    if (author && tutorial.authors.indexOf(author) === -1) {
      return false
    }
    if (keyword && tutorial.labels.application_keyword.indexOf(keyword) === -1) {
      return false
    }
    if (method && tutorial.labels.data_analytics_method.indexOf(method) === -1) {
      return false
    }
    return true
  }

  const tutorials_list = tutorials.tutorials.filter(tutorial => tutorial.labels.application_section[0] === 'Tutorials for artificial-intelligence methods')

  const tutorials_list_beginner = tutorials_list.filter(tutorial => tutorial.labels.category[0] === 'beginner_tutorial')

  const tutorials_list_intermediate = tutorials_list.filter(tutorial => tutorial.labels.category[0] === 'intermediate_tutorial')

  const {authors, keywords, methods} = useMemo(() => {
    const authors = {}
    const keywords = {}
    const methods = {}
    tutorials_list.forEach(tutorial => {
      tutorial.key = tutorial.title.replace(/\W/gm, '_').toLowerCase()
      tutorial.authors.forEach(i => { authors[i] = i })
      tutorial.labels.application_keyword.forEach(i => { keywords[i] = i })
      tutorial.labels.data_analytics_method.forEach(i => { methods[i] = i })
    }
    )
    return {
      authors: Object.keys(authors).sort(),
      keywords: Object.keys(keywords).sort(),
      methods: Object.keys(methods).sort()
    }
  }, [tutorials_list])

  const [valAuthor, setAuthor] = useState({})
  const [valKeyword, setKeyword] = useState({})
  const [valMethod, setMethod] = useState({})

  return <Grid container spacing={1} className={styles.root}>
    <Grid container spacing={0} className={styles.Heading}>
      <Grid item xs={6} className={styles.sectionTitle}>
        <Typography className={styles.title}>
          Learn from tutorials
        </Typography>
        <Typography className={styles.deck}>
          We develop and implement methods that identify correlations and
          structure in big data of materials. This will enable scientists and
          engineers to decide which materials are useful for specific
          applications or which new materials should be the focus of future
          studies. The following tutorials are designed to get started with the
          AI Toolkit.
        </Typography>
      </Grid>
      <Grid item xs={4} className={styles.sectionIcon}>
        <img alt='Tutorials icon' src={TutorialsIcon} className={styles.icon}/>
      </Grid>
    </Grid>
    <Grid container spacing={0}>
      <Grid item xs={12} >
        <Typography className={styles.filter}>
          Filter Tutorials
        </Typography>
      </Grid>
      <Grid item xs={3}>
        <Autocomplete
          id="combo-box-demo"
          options={authors}
          className={styles.autocomplete}
          getOptionLabel={option => option}
          // style={{height: '50px', width: '150px'}}
          renderInput={params => (
            <TextField
              {...params}
              label="Author"
              InputProps={{...params.InputProps, disableUnderline: true}}
              fullWidth
            />
          )}
          value={valAuthor}
          onChange={(_, value) => {
            setQueryParameters({...emptyQuery, author: value})
            setAuthor(value)
          }}
        />
      </Grid>
      <Grid item xs={3}>
        <Autocomplete
          id="combo-box-demo"
          options={keywords}
          // style={{height: '50px', width: '250px'}}
          className={styles.autocomplete}
          getOptionLabel={option => option}
          renderInput={params => (
            <TextField
              {...params}
              label="Keyword"
              InputProps={{...params.InputProps, disableUnderline: true}}
              fullWidth
            />
          )}
          value={valKeyword}
          onChange={(_, value) => {
            setQueryParameters({...emptyQuery, keyword: value})
            setKeyword(value)
          }}
        />
      </Grid>
      <Grid item xs={3}>
        <Autocomplete
          id="combo-box-demo"
          options={methods}
          // style={{height: '50px', width: '250px'}}
          className={styles.autocomplete}
          renderInput={params => (
            <TextField
              {...params}
              label="Method"
              InputProps={{...params.InputProps, disableUnderline: true}}
              fullWidth
            />
          )}
          value={valMethod}
          onChange={(_, value) => {
            setQueryParameters({...emptyQuery, method: value})
            setMethod(value)
          }}
        />
      </Grid>
    </Grid>
    <Grid container spacing={1} className={styles.tutorialsList}>
      <Grid item xs={12}>
        <Grid container spacing={1}>
          <Grid item xs={3}>
            <Typography className={styles.textLevel}>
              BEGINNER LEVEL
            </Typography>
          </Grid>
          <Grid item xs={9}>
            <Divider disableGutters className={styles.tutorialsDivider}></Divider>
          </Grid>
        </Grid>
        <AccordionsList tutorials_list={tutorials_list_beginner}
          author={authors}
          setAuthor = {setAuthor}
          keyword={keywords}
          setKeyword={setKeyword}
          method={methods}
          setMethod={setMethod}
          filter={filter}
          setQueryParameters={setQueryParameters}
          queryParameters={queryParameters}
          emptyQuery={queryParameters} />
      </Grid>
      <Box mt={'100px'}>
        <Grid container spacing={1}>
          <Grid item xs={3}>
            <Typography className={styles.textLevel}>
              INTERMEDIATE LEVEL
            </Typography>
          </Grid>
          <Grid item xs={9}>
            <Divider disableGutters className={styles.tutorialsDivider}></Divider>
          </Grid>
        </Grid>
        <Grid item xs={12}>
          <AccordionsList tutorials_list={tutorials_list_intermediate}
            author={authors}
            setAuthor = {setAuthor}
            keyword={keywords}
            setKeyword={setKeyword}
            method={methods}
            setMethod={setMethod}
            filter={filter}
            setQueryParameters={setQueryParameters}
            queryParameters={queryParameters}
            emptyQuery={queryParameters} />
        </Grid>
      </Box>

    </Grid>
    <Grid item xs={6} className={styles.sectionTitle}>
      <Typography className={styles.titleSecondary}>
        Next advanced level
      </Typography>
      <Typography className={styles.deck}>
        After learning the basics of artificial-intelligence tools, you can apply the latest
        AI developments to timely problems in materials science. These
        outstanding applications allow to reproduce results that have been
        published recently in scientific journals.
      </Typography>
      <Grid container spacing={1}>
        <Grid item xs={4}>
          <IconButton
            href={'aitoolkit'}
            style={{marginRight: '0px', marginTop: '20px'}}
          >
            <img alt='AI toolkit logo' src={FigureAI} style={{width: '120px'}}/>
          </IconButton>
        </Grid>
        <Grid item xs={8}>
          <Button
            width='10px'
            color='#2A3C67'
            component={Link}
            to="reproduce"
            onClick = {() => { setQueryParameters({author: 'Sbailò, Luigi'}) }}
            className={styles.bottomButton}
            endIcon={<img alt='Arrow icon' src={ArrowIcon}/>}
          >
            <Typography className={styles.fieldText}>
              Advanced applications
            </Typography>
          </Button>
        </Grid>
      </Grid>
    </Grid>
    <Grid item xs={4} className={styles.sectionIcon}>
      <img alt='Reproduce icon' src={ReproduceIcon} className={styles.bottomIcon}/>
    </Grid>
  </Grid>
}
