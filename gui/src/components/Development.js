import React from 'react'
import PropTypes from 'prop-types'
import { withStyles } from '@material-ui/core/styles'
import Markdown from './Markdown'
import gitInfo from '../gitinfo'

class Development extends React.Component {
  static propTypes = {
    classes: PropTypes.object.isRequired
  }

  static styles = theme => ({
    root: {},
  })

  render() {
    const { classes } = this.props

    return (
      <div className={classes.root}>
        <Markdown>{`
          # Build info
          - version: \`${gitInfo.version}\`
          - ref: \`${gitInfo.ref}\`
          - last commit message: *${gitInfo.log}*

          \n\n# ELK
          We use a central logging system based on the *elastic*-stack
          (previously *ELK*-stack). This system pushes logs, events, monitoring data,
          and other application metrics to a central **E**lasticsearch, via **L**ogstack,
          where it can be analysed with **K**ibana (hence **ELK**).
          \n\n[Link to Kiaba](/nomadxt/kibana)
        `}</Markdown>
      </div>
    )
  }
}

export default withStyles(Development.styles)(Development)