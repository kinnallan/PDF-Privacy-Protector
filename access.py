import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
import bcrypt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFAccessor:
    def __init__(self):
        self.initialize_firebase()

    def initialize_firebase(self):
        try:
            if not firebase_admin._apps:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                cred_path = os.path.join(current_dir, "pdfblur-firebase-adminsdk-dfic3-3bebd41ba0.json")
                
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at {cred_path}")
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': 'pdfblur.firebasestorage.app'
                })
                
            self.db = firestore.client()
            logger.info("✅ Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise

    def verify_access(self, doc_id, password):
        try:
            doc_ref = self.db.collection('documents').document(doc_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Document {doc_id} not found")
                return None, None, "Document not found"

            doc_data = doc.to_dict()
            
            # Check owner password
            if bcrypt.checkpw(password.encode(), doc_data['owner_password'].encode()):
                logger.info(f"Owner access granted for {doc_id}")
                # Update access count
                doc_ref.update({'access_count': doc_data.get('access_count', 0) + 1})
                return doc_data['filename'], doc_data['original_url'], "owner"
            
            # Check user password
            if bcrypt.checkpw(password.encode(), doc_data['user_password'].encode()):
                logger.info(f"User access granted for {doc_id}")
                # Update access count
                doc_ref.update({'access_count': doc_data.get('access_count', 0) + 1})
                return doc_data['filename'], doc_data['blurred_url'], "user"
            
            logger.warning(f"Invalid password attempt for {doc_id}")
            return None, None, "Invalid password"
            
        except Exception as e:
            logger.error(f"Error verifying access: {str(e)}")
            raise

def main():
    st.set_page_config(page_title="PDF Access", layout="wide")
    st.title("PDF Document Access")
    
    try:
        accessor = PDFAccessor()
        st.success("✅ Connected to Firebase successfully")
    except Exception as e:
        st.error(f"❌ Failed to connect to Firebase: {str(e)}")
        st.stop()
    
    st.write("Access your protected PDF document using your Document ID and password.")
    
    doc_id = st.text_input("Document ID")
    password = st.text_input("Password", type="password")
    
    if st.button("Access Document"):
        if not doc_id or not password:
            st.error("Please enter both Document ID and password")
            return
        
        try:
            filename, url, access_type = accessor.verify_access(doc_id, password)
            
            if url:
                st.success(f"✅ Access granted as {access_type}")
                st.write(f"Document: {filename}")
                st.markdown(f"[Click here to view/download PDF]({url})")
                
                # Show access type info
                if access_type == "owner":
                    st.info("You have full access to the original document.")
                else:
                    st.info("You have access to the protected version with sensitive data masked.")
            else:
                st.error(f"❌ Access denied: {access_type}")
        
        except Exception as e:
            st.error(f"❌ Error accessing document: {str(e)}")

if __name__ == "__main__":
    main()
    