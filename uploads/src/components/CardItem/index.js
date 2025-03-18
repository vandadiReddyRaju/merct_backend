// Write your code here.
import './index.css'

const TechnologyCard = props => {
  const {cardDetails} = props
  const {title, description, imageUrl, className} = cardDetails
  return (
      <li>
        <div className={'card-container ${className}'}>
        <h1 className="card-heading">{title}</h1>
          <p className="card-description">{description}</p>
          <img src="${imageUrl}" className="image-styling" />
        </div>
      </li>
  )
}

export default TechnologyCard
