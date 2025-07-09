# {CSV} FF2API

A comprehensive flat file to API mapping tool designed specifically for freight brokers. This tool allows non-technical users to easily upload freight data files and automatically map them to the freight loads API.

## ✨ Features

- **File Upload Support**: CSV and Excel (.xlsx, .xls) files
- **Automatic Field Mapping**: Intelligent suggestions based on column names
- **Data Validation**: Comprehensive validation before API submission
- **Configuration Storage**: Save mapping configurations for reuse
- **Progress Tracking**: Real-time processing progress with detailed results
- **Error Handling**: Download failed records for troubleshooting
- **Secure Storage**: Encrypted API credentials storage
- **Upload History**: Track all processing activities

## 🏗️ Architecture

- **Frontend**: Streamlit (Python-based web interface)
- **Backend**: FastAPI + SQLite for mapping storage
- **File Processing**: pandas + openpyxl
- **Security**: Encrypted credential storage with cryptography
- **Deployment**: Docker for easy local deployment

## 🚀 Quick Start

### For Team Members (Streamlit Cloud)

The FF2API application is deployed on Streamlit Cloud for team access:

1. **Access the application** at your team's deployment URL
2. **Enter the team password** when prompted
3. **Start using the application** immediately

**Important**: This is a shared environment - all team members use the same database.

### For Administrators (Deployment Setup)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Deployment Commands:**
```bash
# Set up GitHub repository
git remote add origin https://github.com/augmentac/ff2api-tool.git
git branch -M main
git push -u origin main

# Generate encryption key for secrets
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY =', Fernet.generate_key().decode())"
```

### For Local Development

#### Prerequisites

- Docker and Docker Compose installed
- Port 8501 available on your system

#### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd FF2API
   ```

2. **Make the run script executable**
   ```bash
   chmod +x run.sh
   ```

3. **Start the application**
   ```bash
   ./run.sh
   ```

4. **Access the application**
   - Open your browser to `http://localhost:8501`
   - The tool will be ready to use immediately

#### Alternative: Manual Setup

If you prefer to run without Docker:

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create necessary directories**
   ```bash
   mkdir -p data/{uploads,mappings,logs} config
   ```

3. **Run the application**
   ```bash
   streamlit run src/frontend/app.py
   ```

## 📖 User Guide

### Step 1: Initial Setup

1. **Brokerage Name**: Enter a unique brokerage name in the sidebar
2. **API Configuration**: Enter your API base URL and bearer token
3. **Test Connection**: Click "Test API Connection" to verify credentials

### Step 2: File Upload

1. **Upload File**: Click "Choose a CSV or Excel file" and select your data
2. **Review Preview**: Check the file preview to ensure data loaded correctly
3. **File Requirements**:
   - Supported formats: CSV, Excel (.xlsx, .xls)
   - Maximum recommended size: 10MB
   - Ensure data starts from row 1 with headers

### Step 3: Field Mapping

1. **Auto-Mapping**: The tool automatically suggests field mappings
2. **Manual Mapping**: Use dropdown menus to map your columns to API fields
3. **Required Fields**: Ensure all required fields (marked with *) are mapped:
   - `Load Reference Number` (load.brokerageLoadId)
   - `Customer Name` (load.customerName)
   - `Origin City` (load.pickups.0.address.city)
   - `Destination City` (load.dropoffs.0.address.city)

### Step 4: Validation and Processing

1. **Validate**: Click "Validate Mapping" to check for errors
2. **Review Results**: Check validation results and fix any errors
3. **Save Configuration**: Check "Save mapping configuration" for future uploads
4. **Process Data**: Click "Process Data" to send data to the API

### Step 5: Results and Troubleshooting

1. **View Results**: Monitor processing progress and final results
2. **Handle Errors**: Download failed records CSV for troubleshooting
3. **Retry**: Fix data issues and re-upload corrected file

## 📊 Supported Data Fields

### Required Fields
- **Reference Number**: Unique load identifier
- **Customer Name**: Name of the customer/shipper
- **Origin City**: Pickup location city
- **Destination City**: Delivery location city

### Optional Fields
- **Origin State/Zip**: Additional pickup location details
- **Destination State/Zip**: Additional delivery location details
- **Pickup Date**: Ready date for pickup
- **Delivery Date**: Required delivery date
- **Rate**: Load payment amount
- **Miles**: Distance for the load
- **Weight**: Load weight in pounds
- **Commodity**: Description of freight
- **Carrier Name**: Trucking company name
- **Driver Name**: Driver information
- **Equipment Type**: Trailer type required

## 🔧 Data Format Guidelines

### Recommended Column Names (for better auto-mapping)

- **Load Number**: `reference_number`, `ref_num`, `load_id`, `load_number`
- **Origin**: `origin_city`, `pickup_city`, `from_city`
- **Destination**: `destination_city`, `delivery_city`, `to_city`
- **Dates**: `pickup_date`, `delivery_date` (format: YYYY-MM-DD)
- **Rate**: `rate`, `price`, `amount`, `target_cost` (numeric, no currency symbols)
- **Weight**: `weight`, `total_weight`, `pounds`, `lbs`
- **Equipment**: `equipment_type`, `trailer_type`, `truck_type`

### Data Requirements

- **Dates**: Prefer YYYY-MM-DD format
- **Numbers**: No currency symbols or commas
- **Text**: Clean, consistent naming
- **Required Fields**: Must not be empty

## 🛠️ Troubleshooting

### Common Issues

1. **File won't upload**
   - Check file format (CSV/Excel only)
   - Verify file size (<10MB)
   - Ensure file isn't corrupted

2. **API connection failed**
   - Verify API URL is correct (https://api.prod.goaugment.com)
   - Check bearer token validity and permissions
   - Ensure network connectivity

3. **No auto-mapping suggestions**
   - Column names may be too different from standard patterns
   - Map manually using dropdowns

4. **Validation errors**
   - Check required fields are present
   - Verify date formats (YYYY-MM-DD preferred)
   - Ensure numeric fields contain valid numbers

5. **API processing failures**
   - Check API rate limits
   - Verify data formats match API requirements
   - Ensure reference numbers are unique

## 💾 Backup & Recovery (Streamlit Cloud)

### ⚠️ Important Notes

- **Ephemeral Storage**: Data is lost when the container restarts
- **Shared Database**: All team members share the same database
- **Manual Backups**: Regular backups are essential for data preservation

### Daily Backup Routine

1. **End of Day**: Last person downloads backup via sidebar
2. **Save Location**: Store in shared company folder
3. **Filename**: Use provided timestamp format

### Morning Restore Routine

1. **Start of Day**: First person checks if restore is needed
2. **Upload Backup**: Use most recent backup file
3. **Verify Data**: Confirm all configurations are present

**Detailed Instructions**: See [BACKUP_PROCEDURES.md](BACKUP_PROCEDURES.md)

## 👥 Team Workflow

### Shared Environment

- All team members use the same database
- Configurations are shared across the team
- No user isolation or individual accounts

### Best Practices

- **Communicate**: Notify team about major operations
- **Backup Before**: Download backup before large imports
- **Stay Organized**: Use clear naming conventions
- **Monitor Status**: Watch container age and backup recommendations

## 🔒 Security

- Simple password protection for team access
- Bearer tokens are encrypted and stored in shared database
- All data processing happens in Streamlit Cloud environment
- No persistent storage - data depends on regular backups

## 🧹 Maintenance

### File Locations
- **Logs**: `logs/` directory for detailed operation logs
- **Uploaded Files**: `data/uploads/` directory
- **Configuration**: `data/freight_loader.db` SQLite database
- **Encryption Key**: `config/encryption.key`

### Commands
- **Stop Application**: `docker-compose down`
- **View Logs**: `docker-compose logs -f`
- **Update**: Pull latest version and run `docker-compose build`

### Backup
Regular backup of these directories is recommended:
- `data/` - Contains all uploaded files and configurations
- `config/` - Contains encryption keys

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs in the `logs/` directory
3. Verify your bearer token and connectivity
4. Ensure file formats meet the requirements

## 📝 License

This project is designed for freight brokers to streamline their data upload processes.

---

**Note**: This tool is designed to work with the GoAugment Loads API. Ensure you have a valid bearer token before use. # Force rebuild - Wed Jul  9 10:19:39 CDT 2025
