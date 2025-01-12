A secure document management system that provides controlled access to PDF documents with different levels of visibility using Firebase Cloud Storage. The system consists of two Streamlit web interfaces - one for administrators to manage documents and another for users to access them.


Features

Admin Interface: Upload PDFs and set access controls

Set user and owner passwords

Generate unique document IDs

Store documents securely in Firebase Cloud Storage

Apply content blurring for restricted access


User Interface: Access documents with appropriate permissions

Enter document ID and password for access

View blurred version with user password

Access original document with owner password



System Architecture
The application is built using:

Streamlit for web interfaces

Firebase Cloud Storage for document storage

PDF processing libraries for document manipulation

Security features for access control


Setup Instructions

1. Install required dependencies: pip install -r requirements.txt

2. Firebase Setup:

Create a Firebase project

Generate your Firebase Admin SDK credentials

Save the credentials file (e.g., pdfblur-firebase-adminsdk-dfic3-3bebd41ba0.json) in the environment folder


Environment Configuration:

Ensure your Firebase credentials file is properly placed

Update any configuration files with your Firebase project details



Usage

1. Admin Interface

Run the admin interface: streamlit run upload.py

Through the admin interface, you can:

Upload PDF documents

Set user passwords (for restricted access)

Set owner passwords (for full access)

Generate and manage document IDs

Store documents in Firebase Cloud Storage



2. User Interface

Run the user interface: streamlit run access.py

To access documents:

Enter the provided document ID

Enter either:

User password (shows blurred sensitive content)

Owner password (shows original document)


Note:

Firebase credentials are not included in this repository for security reasons

Users must add their own Firebase credentials file in the environment folder

Proper password management and distribution is essential for security

Document IDs should be shared securely with intended users


- PDF Privacy Protector offers a robust solution for organizations needing to manage sensitive documents with different levels of access control. By leveraging Firebase Cloud Storage and implementing a dual-password system, it provides a secure and flexible way to share documents while protecting sensitive information. The combination of user-friendly Streamlit interfaces and strong security measures makes it suitable for various use cases, from legal document sharing to confidential business reports.
