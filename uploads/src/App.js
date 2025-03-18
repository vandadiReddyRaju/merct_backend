import './App.css'
import TechnologyCard from './components/CardItem'

const cardsList = [
  {
    id: 1,
    title: 'Data Scientist',
    description:
      'Data scientists gather and analyze large sets of structured and unstructured data',
    imgUrl: 'https://assets.ccbp.in/frontend/react-js/data-scientist-img.png',
    className: 'card-1',
  },
  {
    id: 2,
    title: 'IOT Developer',
    description:
      'IoT Developers are professionals who can develop, manage, and monitor IoT devices.',
    imgUrl: 'https://assets.ccbp.in/frontend/react-js/iot-developer-img.png',
    className: 'card-2',
  },
  {
    id: 3,
    title: 'VR Developer',
    description:
      'A VR developer creates completely new digital environments that people can see.',
    imgUrl: 'https://assets.ccbp.in/frontend/react-js/vr-developer-img.png',
    className: 'card-3',
  },
  {
    id: 4,
    title: 'ML Engineer',
    description:
      'Machine learning engineers feed data into models defined by data scientists.',
    imgUrl: 'https://assets.ccbp.in/frontend/react-js/ml-engineer-img.png',
    className: 'card-4',
  },
]

const App = () => (
  <div className="technology-container">
    <h1 className="main-heading">Learn 4.0 Technology</h1>
    <p className="main-description">
      Get trained by alumini of IITs and top comapanies like
      Amazon,Microsoft,Intel,Nvidia,Qualcomm etc. Learn directly from
      proffessionals involved in Product Development.{' '}
    </p>
    <ul className="technology-card-list">
      {cardsList.map(eachItem => (
        <TechnologyCard cardDetails={eachItem} key={eachItem.id} />
      ))}
    </ul>
  </div>
)

export default App
