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
import React, { useEffect, useContext, useState, useCallback } from 'react'
import PropTypes from 'prop-types'
import { Typography, Box, Grid, Chip, IconButton, Tooltip, makeStyles, useTheme } from '@material-ui/core'
import { useErrors } from '../errors'
import Browser, { Item, Content, Adaptor, laneContext } from './Browser'
import ViewIcon from '@material-ui/icons/Search'
import DownloadIcon from '@material-ui/icons/CloudDownload'
import FolderIcon from '@material-ui/icons/Folder'
import FileIcon from '@material-ui/icons/AssignmentOutlined'
import Download from '../entry/Download'
import Quantity from '../Quantity'
import InfiniteScroll from 'react-infinite-scroller'
import { useApi } from '../api'

const useStyles = makeStyles(theme => ({
  fileContents: {
    width: 600,
    overflowX: 'auto',
    color: theme.palette.primary.contrastText,
    backgroundColor: theme.palette.primary.dark,
    marginTop: theme.spacing(1),
    padding: '0px 6px',
    fontFamily: 'Consolas, "Liberation Mono", Menlo, Courier, monospace',
    fontSize: 12
  }
}))

const FileBrowser = React.memo(({uploadId, path}) => {
  const adaptor = new RawDirectoryAdaptor(uploadId, path)
  return <Browser adaptor={adaptor} />
})
FileBrowser.propTypes = {
  uploadId: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired
}
export default FileBrowser

class RawDirectoryAdaptor extends Adaptor {
  constructor(uploadId, path) {
    super()
    this.uploadId = uploadId
    this.path = path
    this.data = undefined // Will be set by RawDirectoryContent component when loaded
  }
  isLoaded() {
    return this.data !== undefined
  }
  itemAdaptor(key) {
    const ext_path = this.path ? this.path + '/' + key : key
    const element = this.data.elementsByName[key]
    if (element) {
      if (element.is_file) {
        return new RawFileAdaptor(this.uploadId, ext_path, element)
      } else {
        return new RawDirectoryAdaptor(this.uploadId, ext_path)
      }
    }
    throw new Error('Bad path: ' + key)
  }
  render() {
    return <RawDirectoryContent uploadId={this.uploadId} path={this.path}/>
  }
}

function RawDirectoryContent({uploadId, path}) {
  const {api} = useApi()
  const {raiseError} = useErrors()
  const lane = useContext(laneContext)
  const [, setLoadedPath] = useState()

  useEffect(() => {
    lane.adaptor.data = undefined
    const encodedPath = path.split('/').map(segment => encodeURIComponent(segment)).join('/')
    api.get(`/uploads/${uploadId}/rawdir/${encodedPath}?include_entry_info=true&page_size=500`)
      .then(response => {
        const elementsByName = {}
        response.directory_metadata.content.forEach(element => { elementsByName[element.name] = element })
        lane.adaptor.data = {response, elementsByName}
        lane.update()
        setLoadedPath(path)
      })
      .catch(error => {
        raiseError(error)
      })
  }, [uploadId, path, setLoadedPath, lane, api, raiseError])

  if (lane.adaptor.data === undefined) {
    return <Content key={path}><Typography>loading ...</Typography></Content>
  } else {
    // Data loaded
    return (
      <Content key={path}>
        {
          lane.adaptor.data.response.directory_metadata.content.map(element => (
            <Item itemKey={element.name} key={path ? path + '/' + element.name : element.name}>
              {
                element.is_file
                  ? <Box display="flex" flexDirection="row" alignItems="start">
                    <FileIcon/>
                    {
                      element.parser_name
                        ? <React.Fragment>
                          <Typography><b>{element.name}&nbsp;</b></Typography>
                          <Chip
                            size="small" padding="30px" color="secondary"
                            label={element.parser_name.replace('parsers/', '')} />
                        </React.Fragment>
                        : <Typography>{element.name}</Typography>
                    }
                  </Box>
                  : <Box display="flex" flexDirection="row" alignItems="start">
                    <FolderIcon/>
                    <Typography><b>{element.name}</b></Typography>
                  </Box>
              }
            </Item>))
        }
        {
          lane.adaptor.data.response.pagination.total > 500 &&
            <Typography color="error">Only showing the first 500 rows</Typography>
        }
      </Content>)
  }
}
RawDirectoryContent.propTypes = {
  uploadId: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired
}

class RawFileAdaptor extends Adaptor {
  constructor(uploadId, path, data) {
    super()
    this.uploadId = uploadId
    this.path = path
    this.data = data
  }
  render() {
    return <RawFileContent uploadId={this.uploadId} path={this.path} data={this.data} key={this.path}/>
  }
}

function RawFileContent({uploadId, path, data}) {
  const lane = useContext(laneContext)
  const [previewing, setPreviewing] = useState(false)

  // A nicer, human-readable size string
  let niceSize, unit, factor
  if (data.size > 1e9) {
    [unit, factor] = ['GB', 1e9]
  } else if (data.size > 1e6) {
    [unit, factor] = ['MB', 1e6]
  } else if (data.size > 1e3) {
    [unit, factor] = ['kB', 1e3]
  }
  if (unit) {
    if (data.size / factor > 100) {
      // No decimals
      niceSize = `${Math.round(data.size / factor)} ${unit} (${data.size} bytes)`
    } else {
      // One decimal
      niceSize = `${Math.round(data.size * 10 / factor) / 10} ${unit} (${data.size} bytes)`
    }
  } else {
    // Unit = bytes
    niceSize = `${data.size} bytes`
  }
  const encodedPath = path.split('/').map(segment => encodeURIComponent(segment)).join('/')
  const downloadUrl = `uploads/${uploadId}/raw/${encodedPath}`
  return (
    <Content key={path}>
      <Grid container justifyContent="flex-end" alignItems="center">
        <Grid item style={{flexGrow: 1}}>
          <Typography variant="h6">Raw file</Typography>
        </Grid>
        <Grid item>
          <Tooltip title='Show contents'>
            <IconButton onClick={() => { setPreviewing(!previewing) }} color={previewing ? 'default' : 'secondary'}>
              <ViewIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <Download component={IconButton} disabled={false}
            color="secondary"
            tooltip="download this file"
            url={downloadUrl}
            fileName={data.name}>
            <DownloadIcon />
          </Download>
        </Grid>
      </Grid>
      <Quantity quantity="filename" data={{filename: data.name}} label="file name" noWrap ellipsisFront withClipboard />
      <Quantity quantity="path" data={{path: path}} label="full path" noWrap ellipsisFront withClipboard />
      <Quantity quantity="filesize" data={{filesize: niceSize}} label="file size" />
      { data.parser_name && <Quantity quantity="parser" data={{parser: data.parser_name}} />}
      { data.parser_name && <Quantity quantity="entryId" data={{entryId: data.entry_id}} noWrap withClipboard />}
      { previewing && <FilePreviewText uploadId={uploadId} path={path} scrollParent={lane.containerRef}/>}
    </Content>)
}
RawFileContent.propTypes = {
  uploadId: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired
}

function FilePreviewText({uploadId, path, scrollParent}) {
  const theme = useTheme()
  const classes = useStyles(theme)
  const {raiseError} = useErrors()
  const [fileContents, setFileContents] = useState(null)
  const {api} = useApi()
  const encodedPath = path.split('/').map(segment => encodeURIComponent(segment)).join('/')

  useEffect(() => {
    if (fileContents === null) {
      // Load the first chunk of the file
      api.get(
        `/uploads/${uploadId}/raw/${encodedPath}`,
        {length: 16 * 1024, decompress: true},
        {transformResponse: []})
        .then(contents => setFileContents({
          hasMore: true,
          contents: contents
        }))
        .catch(raiseError)
    }
  }, [uploadId, encodedPath, fileContents, setFileContents, api, raiseError])

  const handleLoadMore = useCallback((page) => {
    // The infinite scroll component has the issue if calling load more whenever it
    // gets updates, therefore calling this infinitely before it gets any chances of
    // receiving the results (https://github.com/CassetteRocks/react-infinite-scroller/issues/163).
    // Therefore, we have to set hasMore to false first and set it to true again after
    // receiving actual results.
    setFileContents(prevState => { return {...prevState, hasMore: false} })
    const initialUploadId = uploadId

    if (fileContents.contents.length < (page + 1) * 16 * 1024) {
      api.get(
        `/uploads/${uploadId}/raw/${encodedPath}`,
        {offset: page * 16 * 1024, length: 16 * 1024, decompress: true},
        {transformResponse: []})
        .then(contents => {
          // The back-button navigation might cause a scroll event, might cause to loadmore,
          // will set this state, after navigation back to this page, but potentially
          // different entry.
          if (initialUploadId === uploadId) {
            setFileContents({
              hasMore: contents.length > 0,
              contents: ((fileContents && fileContents.contents) || '') + contents
            })
          }
        })
        .catch(error => {
          setFileContents(null)
          raiseError(error)
        })
    }
  }, [api, uploadId, encodedPath, fileContents, raiseError])

  if (fileContents === null) {
    return <Typography>Loading ...</Typography>
  } else if (fileContents && fileContents.contents !== null) {
    return <React.Fragment>
      <Typography variant="h6">File contents</Typography>
      <InfiniteScroll
        className={classes.fileContents}
        pageStart={0}
        loadMore={handleLoadMore}
        hasMore={fileContents.hasMore}
        useWindow={false}
        getScrollParent={() => scrollParent.current}
      >
        <pre style={{margin: 0}}>
          {`${fileContents.contents}`}
          &nbsp;
        </pre>
      </InfiniteScroll>
    </React.Fragment>
  }
  return <Typography color="error">Cannot display file due to unsupported file format.</Typography>
}
FilePreviewText.propTypes = {
  uploadId: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  scrollParent: PropTypes.object.isRequired
}
