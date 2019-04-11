import React from 'react'
import PropTypes from 'prop-types'
import { withStyles, Card, CardHeader, CardContent } from '@material-ui/core'
import RawFiles from '../entry/RawFiles'

class DFTEntryCards extends React.Component {
  static propTypes = {
    classes: PropTypes.object.isRequired,
    data: PropTypes.object.isRequired,
    loading: PropTypes.bool
  }

  static styles = theme => ({
    root: {}
  })

  render() {
    const { classes, data: {upload_id, calc_id, files} } = this.props

    return (
      <Card className={classes.root}>
        <CardHeader title="Raw files" />
        <CardContent classes={{root: classes.cardContent}}>
          <RawFiles uploadId={upload_id} calcId={calc_id} files={files || []} />
        </CardContent>
      </Card>
    )
  }
}

export default withStyles(DFTEntryCards.styles)(DFTEntryCards)