# Paperless Auto Uploader

A Python-based desktop application that automatically monitors a folder and uploads new documents to your Paperless-ngx server. Perfect for automating document digitization workflows from scanners, email attachments, or any folder-based document input.

## 🎯 Features

- **📁 Folder Monitoring**: Real-time monitoring of a specified folder for new documents
- **⚡ Automatic Upload**: Instantly uploads new files to your Paperless-ngx server via API
- **🖥️ GUI Interface**: User-friendly graphical interface for easy configuration
- **🚀 Background Mode**: Run silently in the background with system tray integration
- **📋 Smart Processing**: Handles existing files and prevents duplicate uploads
- **📂 File Organization**: Automatically moves processed files to a "processed" subfolder
- **🔍 Connection Testing**: Built-in connection testing to verify server connectivity
- **💾 Configuration Persistence**: Saves settings for future use
- **📝 Detailed Logging**: Comprehensive logging of all operations

## 🔧 Supported File Types

- **PDF** documents (`.pdf`)
- **Images**: PNG, JPG, JPEG, TIFF, TIF (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`)
- **Text** documents (`.txt`)
- **Word** documents (`.doc`, `.docx`)

## 📋 Requirements

- Python 3.7+
- Paperless-ngx server with API access
- Valid API token from your Paperless instance

## 🚀 Installation

### Method 1: Run from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/paperless-auto-uploader.git
   cd paperless-auto-uploader
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv env
   env\Scripts\activate  # On Windows
   # or
   source env/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python paperless_monitor.py
   ```

### Method 2: Create Executable

1. **Follow steps 1-3 above**

2. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

3. **Build executable:**
   ```bash
   python -m PyInstaller --onefile --windowed paperless_monitor.py
   ```

4. **Find executable in `dist/` folder**

## ⚙️ Configuration

1. **Launch the application**
2. **Configure settings:**
   - **Paperless Server**: URL of your Paperless-ngx instance (e.g., `https://paperless.yourdomain.com`)
   - **API Token**: Generate from your Paperless admin panel (Admin → Tokens)
   - **Monitor Folder**: Choose the folder to monitor for new documents

3. **Test connection** to verify settings
4. **Save configuration** for future use

## 🎮 Usage

### Basic Workflow

1. **Start monitoring** by clicking "▶️ Start Monitoring"
2. **Process existing files** (optional) when prompted
3. **Add new documents** to the monitored folder
4. **Files are automatically uploaded** to Paperless
5. **Processed files** are moved to the `processed/` subfolder

### Background Mode

1. **Start monitoring** normally
2. **Click "🚀 Execute in Background"**
3. **Application minimizes** to system tray
4. **Right-click tray icon** to access controls
5. **Files continue uploading** automatically

### Advanced Features

- **📂 Process Existing Files**: Manually process files already in the folder
- **🧹 Clear Processed List**: Reset the list of processed files (allows re-upload)
- **👁️ Show Interface**: Restore window from background mode

## 📁 Folder Structure

```
Your Monitor Folder/
├── document1.pdf          ← New files (will be uploaded)
├── invoice.jpg           ← New files (will be uploaded)
└── processed/            ← Processed files (moved here after upload)
    ├── document1.pdf
    └── invoice.jpg
```

## 🔑 Getting Your API Token

1. **Access your Paperless admin panel**: `https://your-paperless-server/admin/`
2. **Navigate to**: Authentication and Authorization → Tokens
3. **Create new token** for your user
4. **Copy the token** and paste it in the application

## 🛠️ Technical Details

### Dependencies

- **watchdog**: File system monitoring
- **requests**: HTTP API communication
- **tkinter**: GUI framework (included with Python)
- **pystray**: System tray integration
- **pillow**: Image processing for tray icon

### File Processing Logic

1. **Detection**: New files are detected via filesystem events
2. **Validation**: File type validation against supported formats
3. **Duplicate Check**: Prevents re-uploading previously processed files
4. **Upload**: Secure upload via Paperless API
5. **Organization**: Moves processed files to subfolder
6. **Logging**: Records all operations for troubleshooting

## 🐛 Troubleshooting

### Connection Issues
- Verify server URL is correct and accessible
- Check API token is valid and has proper permissions
- Ensure firewall/network allows connection to Paperless server

### File Not Uploading
- Check file format is supported
- Verify file isn't empty or corrupted
- Check logs for specific error messages
- Ensure sufficient disk space in monitor folder

### Background Mode Issues
- On some systems, Windows Defender may flag the executable
- Add exception in antivirus software if necessary
- Ensure system tray is enabled in Windows settings

## 📝 Logs

The application creates detailed logs in:
- **GUI Log**: Real-time log display in the interface
- **File Log**: `paperless_uploader.log` in the application directory
- **Processed Files**: `processed_files.txt` tracks uploaded files

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) team for the excellent document management system
- [Watchdog](https://github.com/gorakhargosh/watchdog) library for file system monitoring
- Python community for the excellent ecosystem

## 📞 Support

If you encounter any issues or have questions:

1. **Check the logs** for error messages
2. **Review troubleshooting section** above
3. **Open an issue** on GitHub with:
   - Description of the problem
   - Steps to reproduce
   - Log files (remove sensitive information)
   - System information (OS, Python version)

---

⭐ **If this project helps you, please consider giving it a star!** ⭐