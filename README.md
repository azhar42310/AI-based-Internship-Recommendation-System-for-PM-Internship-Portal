
<!-- # PM Internship Recommendation System -->

An AI-powered internship recommendation engine designed specifically for the PM Internship Scheme, helping students from diverse backgrounds find relevant internship opportunities.

## Features

### 🎯 Core Functionality
- **AI-Powered Matching**: Advanced algorithms analyze user profiles to suggest the most relevant internships
- **User Authentication**: Secure registration and login system
- **Profile Management**: Comprehensive user profiles with skills, education, and preferences
- **Resume Parsing**: Automatic skill extraction from uploaded resumes (planned)
- **Mobile-First Design**: Optimized for mobile devices with intuitive UI

### 🎨 User Experience
- **Visual-First Interface**: Minimal text with icons and visual cues
- **Regional Language Support**: Ready for multi-language implementation
- **Low Digital Literacy Friendly**: Designed for first-generation learners
- **Responsive Design**: Works seamlessly across all devices

### 🔧 Technical Features
- **Flask Backend**: Lightweight and scalable web framework
- **SQLite Database**: Efficient data storage and retrieval
- **CSV Data Import**: Automatic import of internship data
- **Recommendation Engine**: Weighted matching algorithm based on:
  - Skills alignment
  - Location preferences
  - Duration preferences
  - Education background

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or Download the Project**
   ```bash
   # If using git
   git clone <repository-url>
   cd InternshipRecommendationSystem
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The application will automatically create the database and import internship data

## Usage Guide

### For Students

1. **Registration**
   - Click "Register" on the homepage
   - Create an account with username, email, and password

2. **Profile Setup**
   - Complete your profile with personal information
   - Add your education details and stream
   - List your skills, certifications, and projects
   - Set your location preference

3. **Get Recommendations**
   - Visit the recommendations page
   - View personalized internship suggestions
   - Apply to internships that match your profile

### For Administrators

1. **Data Management**
   - Update `IntershipDataset.csv` with new internship data
   - Restart the application to import new data
   - Monitor user registrations and profile completions

## Project Structure

```
InternshipRecommendationSystem/
├── app.py                          # Main Flask application
├── requirements.txt               # Python dependencies
├── IntershipDataset.csv          # Internship data source
├── templates/                     # HTML templates
│   ├── base.html                 # Base template with navigation
│   ├── index.html                # Homepage
│   ├── register.html             # Registration page
│   ├── login.html                # Login page
│   ├── dashboard.html            # User dashboard
│   ├── profile.html              # Profile management
│   └── recommendations.html      # Recommendation display
└── README.md                     # This file
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Encrypted password
- `full_name`: User's full name
- `phone`: Contact number
- `education_level`: Education qualification
- `stream`: Academic stream/field
- `skills`: JSON array of skills
- `certifications`: JSON array of certifications
- `projects`: JSON array of projects
- `location_preference`: Preferred work location
- `resume_path`: Path to uploaded resume
- `created_at`: Account creation timestamp

### Internships Table
- `id`: Primary key
- `title`: Internship title
- `company_name`: Company name
- `location`: Work location
- `start_date`: Internship start date
- `duration`: Internship duration
- `stipend`: Compensation details
- `status`: Application status
- `skills_required`: Required skills
- `apply_by`: Application deadline
- `about_internship`: Internship description
- `who_can_apply`: Eligibility criteria
- `about_company`: Company information
- `end_date`: Internship end date

## Recommendation Algorithm

The recommendation engine uses a weighted scoring system:

1. **Skills Matching (50 points)**
   - Calculates overlap between user skills and required skills
   - Higher score for better skill alignment

2. **Location Preference (20 points)**
   - Bonus for location matches
   - Partial credit for "Work From Home" options

3. **Duration Preference (10 points)**
   - Preference for shorter internships (1-2 months)
   - Suitable for student schedules

4. **Additional Factors**
   - Education level compatibility
   - Stream relevance
   - Application deadline proximity

## Future Enhancements

### Phase 2 Features
- **Resume Parsing**: PDF/DOC resume analysis
- **Advanced AI**: Machine learning-based recommendations
- **Multi-language Support**: Regional language interface
- **Email Notifications**: New internship alerts
- **Application Tracking**: Track application status

### Phase 3 Features
- **Company Dashboard**: For employers to post internships
- **Video Interviews**: Integrated interview scheduling
- **Skill Assessment**: Online skill evaluation tests
- **Mentorship Program**: Connect with industry mentors
- **Analytics Dashboard**: Usage and success metrics

## Technical Specifications

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Icons**: Font Awesome
- **Data Processing**: Pandas, scikit-learn
- **Security**: Werkzeug password hashing

## Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set up a production WSGI server (Gunicorn)
2. Configure reverse proxy (Nginx)
3. Set up SSL certificates
4. Configure environment variables
5. Set up database backups

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## License

This project is developed for the PM Internship Scheme and is intended for educational and governmental use.

---

**Built with ❤️ for the PM Internship Scheme**
