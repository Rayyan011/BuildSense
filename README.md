# BuildSense: AI-Powered Urban Development Recommender

![BuildSense Logo](static/style.css)

BuildSense is an advanced machine learning system that provides data-driven recommendations for urban development in Hulhumalé, Maldives. By analyzing geospatial data and urban patterns, it suggests optimal development types (Café, Park, Clinic, or Residential) for specific locations.

## �� Key Features

- **Synthetic Data Generation**: Currently uses sophisticated synthetic data generation with realistic patterns
- **Real-time Data Ready**: Architecture designed to seamlessly transition to real OpenStreetMap data
- **Machine Learning Pipeline**: Implements a sophisticated RandomForest classifier with feature engineering
- **Intelligent Caching**: Optimized API query caching for improved performance
- **Interactive Visualization**: Modern, responsive web interface with Leaflet.js integration
- **Explainable AI**: Provides confidence scores and feature importance explanations
- **Production-Ready Architecture**: FastAPI backend with robust error handling

## 🏗️ Technical Architecture

### Backend Stack
- **FastAPI**: High-performance async web framework
- **Scikit-learn**: Machine learning pipeline and model training
- **Pandas/NumPy**: Data processing and feature engineering
- **Overpass API**: Ready for real-time geospatial data retrieval
- **Joblib**: Model serialization and caching

### Frontend Stack
- **Leaflet.js**: Interactive map visualization
- **Font Awesome**: Professional iconography
- **Modern CSS**: Responsive design with animations
- **JavaScript**: Dynamic UI updates and API integration

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/buildsense.git
   cd buildsense
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Data Collection & Model Training

1. Generate synthetic data (current implementation):
   ```bash
   python generate_synthetic_data.py
   ```
   This script:
   - Creates realistic synthetic data with spatial patterns
   - Simulates POI distributions based on urban planning principles
   - Generates balanced datasets for model training
   - Saves data to CSV for model training

2. Train the model:
   ```bash
   python train_model.py
   ```
   Features:
   - Automated data preprocessing
   - Feature standardization
   - Model serialization
   - Performance metrics

### Running the Application

1. Start the server:
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the application:
   - Web Interface: http://127.0.0.1:8000
   - API Documentation: http://127.0.0.1:8000/docs

## 🎯 Use Cases

- **Urban Planning**: Data-driven development recommendations
- **Real Estate**: Location analysis for property development
- **Business Intelligence**: Site selection for new establishments
- **City Management**: Infrastructure planning and optimization

## 🔍 How It Works

1. **Data Generation/Collection**:
   - **Current**: Sophisticated synthetic data generation with realistic spatial patterns
   - **Future**: Grid-based sampling of Hulhumalé with real OpenStreetMap data
   - POI density analysis
   - Feature engineering (foot traffic, road proximity)
   - Intelligent caching system

2. **Model Training**:
   - RandomForest classifier with 100 trees
   - Feature standardization
   - Cross-validation
   - Model persistence

3. **Prediction Pipeline**:
   - **Current**: Synthetic feature generation based on location
   - **Future**: Real-time geospatial data retrieval from OpenStreetMap
   - Feature extraction
   - Model inference
   - Confidence scoring
   - Explanation generation

## 📊 Performance

- **Accuracy**: High prediction accuracy on synthetic test data
- **Latency**: < 500ms response time
- **Scalability**: Efficient caching reduces API load
- **Reliability**: Robust error handling and retries

## 🔄 Extending to Real-Time Data

The current implementation uses sophisticated synthetic data generation to demonstrate the system's capabilities. To extend to real-time data:

1. Uncomment the Overpass API query code in `api.py`
2. Run `collect_real_data.py` to gather real OpenStreetMap data
3. Retrain the model with the real data
4. The application architecture is designed for this transition with minimal changes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenStreetMap contributors
- Overpass API team
- Scikit-learn community
- FastAPI developers

---

Built with ❤️ for urban development


