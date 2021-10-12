import {makeStyles} from '@material-ui/core'
import Background from './assets/AIT_bg_title.jpg'

const useStylesList = makeStyles(theme => ({

  root: {
    margin: theme.spacing(3),
    width: '100%',
    marginLeft: 'auto',
    marginRight: 'auto',
    maxWidth: '1052px'
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
    fontWeight: 'bold',
    color: '#2A3C67',
    fontSize: '35px',
    marginLeft: '-10px',
    fontFamily: 'TitilliumBold',
    marginTop: '-70px'
  },
  deck: {
    color: '#2A3C67',
    fontSize: '22px',
    marginTop: '20px',
    lineHeight: '30px',
    marginLeft: '-10px',
    fontFamily: 'TitilliumRegular',
    width: '518px'
  },
  icon: {
    height: '371px',
    marginTop: '-20px',
    marginLeft: '100px'
  },
  filter: {
    fontWeight: 'bold',
    color: '#2A3C67',
    fontSize: '20px',
    marginTop: '60px',
    marginLeft: '0px',
    fontFamily: 'TitilliumBold'
  },
  autocomplete: {
    height: 'auto',
    color: '#2A3C67',
    border: '3px solid rgba(127, 239, 239, 1)',
    borderRadius: '10px 10px 10px 10px',
    marginTop: '10px',
    marginLeft: '0px'
  },
  tutorialsList: {
    marginTop: '50px'
  },
  tutorialTitleGrid: {
    marginRight: '40px'
  },
  tutorialTitleText: {
    fontSize: '28px',
    color: '#2A3C67',
    fontFamily: 'TitilliumBold',
    lineHeight: '30px'
  },
  authorsGrid: {
    marginLeft: '150px',
    marginRight: '30px'
  },
  fieldText: {
    color: '#2A3C67'
  },
  linkAuthors: {
    color: '#2A3C67',
    cursor: 'pointer',
    fontFamily: 'TitilliumRegular',
    lineHeight: '20px',
    fontSize: '16px'
  },
  tutorialDescriptionGrid: {
    marginLeft: '50px'
  },
  tutorialDescriptionText: {
    fontFamily: 'TitilliumRegular',
    color: '#2A3C67',
    fontSize: '18px'
  },
  keyworksGrid: {
    marginLeft: '80px'
  },
  linkKeywords: {
    border: '1.5px solid rgba(127, 239, 239, 1)',
    lineHeight: '35px',
    color: '#2A3C67',
    cursor: 'pointer',
    fontStyle: 'normal',
    fontFamily: 'TitilliumRegular',
    fontSize: '16px'
  },
  textLevel: {
    textAlign: 'left',
    color: 'rgba(127, 239, 239, 1)',
    fontSize: '22px',
    height: '22px',
    fontFamily: 'TitilliumRegular',
    marginTop: '-16px'
  },
  tutorialsDivider: {
    backgroundColor: 'rgba(127, 239, 239, 1)',
    height: '13px',
    borderRadius: '4px'
  },
  tutorialActions: {
    marginLeft: '50px'
  },
  tutorialResources: {
    marginTop: '-17px',
    marginLeft: '-6px'
  },
  titleSecondary: {
    fontWeight: 'bold',
    color: 'rgba(127, 239, 239, 1)',
    fontSize: '35px',
    marginLeft: '-10px',
    fontFamily: 'TitilliumRegular'
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
    lineHeight: '20px',
    fontFamily: 'TitilliumBold'
  },
  bottomIcon: {
    height: '300px',
    marginTop: '80px',
    marginLeft: '120px'
  }
}))

const useStylesLanding = makeStyles(theme => ({
  root: {
    width: '100%',
    maxWidth: 'auto',
    backgroundImage: `url(${Background})`,
    color: 'white',
    height: '1000px'
  },
  boxIcons: {
    width: '1000px',
    margin: 'auto',
    marginTop: '-200px'
  },
  title: {
    fontSize: '50px',
    margin: 'auto',
    textAlign: 'center',
    align: 'center',
    marginTop: '200px',
    width: '450px',
    height: '140px',
    fontFamily: 'TitilliumBold',
    letterSpacing: 0,
    wordSpacing: '10px',
    lineHeight: '60px',
    color: 'white'
  },
  deck: {
    fontFamily: 'TitilliumRegular',
    letterSpacing: 0,
    marginTop: '-200px',
    wordSpacing: '5px',
    lineHeight: '30px',
    color: 'white',
    fontSize: '30px',
    margin: 'auto',
    textAlign: 'center',
    align: 'center',
    left: '736px',
    top: '270px',
    width: '500px',
    height: '140px'
  },
  button: {
    backgroundColor: 'white',
    fontSize: 20,
    fontFamily: 'TitilliumBold',
    color: '#2A3C67',
    textAlign: 'center',
    align: 'center',
    borderRadius: '25px',
    width: '200px',
    height: '70px',
    lineHeight: '20px'

  },
  link: {
    cursor: 'pointer'
  }
}))

export { useStylesList }
export { useStylesLanding }
