A secure document management system that provides controlled access to PDF documents with different levels of visibility using Firebase Cloud Storage. The system consists of two Streamlit web interfaces - one for administrators to manage documents and another for users to access them.



1. Features

a) Admin Interface: 

To run: streamlit run upload.py

Upload PDFs and set access controls

Set user and owner passwords

Generate unique document IDs

Store documents securely in Firebase Cloud Storage

Can control blur intensity (scale of 5-20)



b) User Interface: 

To run: streamlit run access.py

Access documents with appropriate permissions

Enter document ID and password for access

View blurred version with user password

Access original document with owner password



2. System Architecture
   
The application is built using:

Streamlit for web interfaces

Firebase Cloud Storage for document storage

PDF processing libraries for document manipulation

Security features for access control


3. Setup Instructions

a) Install required dependencies: pip install -r requirements.txt

b) Firebase Setup:

Create a Firebase project

Generate your Firebase Admin SDK credentials

Save the credentials file (e.g., pdfblur-firebase-adminsdk-dfic3-3bebd41ba0.json) in the environment folder


4. Environment Configuration:

Ensure your Firebase credentials file is properly placed

Update any configuration files with your Firebase project details



5. Note:

Firebase credentials are not included in this repository for security reasons

Users must add their own Firebase credentials file in the environment folder

Proper password management and distribution is essential for security

Document IDs should be shared securely with intended users


- PDF Privacy Protector offers a robust solution for organizations needing to manage sensitive documents with different levels of access control. By leveraging Firebase Cloud Storage and implementing a dual-password system, it provides a secure and flexible way to share documents while protecting sensitive information. The combination of user-friendly Streamlit interfaces and strong security measures makes it suitable for various use cases, from legal document sharing to confidential business reports.
