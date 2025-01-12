import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFilter
import re
import tempfile
import os
from io import BytesIO
import firebase_admin
from firebase_admin import credentials, storage, firestore
import uuid  # Added this import
import bcrypt
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFMasker:
    def __init__(self):
        self.patterns = {
            'phone': r'\b(\+?\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
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
            self.bucket = storage.bucket()
            logger.info("✅ Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise

    def check_doc_id_exists(self, doc_id):
        doc_ref = self.db.collection('documents').document(doc_id)
        return doc_ref.get().exists

    def find_sensitive_data(self, page):
        sensitive_areas = []
        page_dict = page.get_text("dict")
        
        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span["text"]
                    bbox = span["bbox"]
                    
                    for pattern_name, pattern in self.patterns.items():
                        if re.search(pattern, text):
                            sensitive_areas.append({
                                'rect': bbox,
                                'text': text,
                                'type': pattern_name
                            })
        
        return sensitive_areas

    def apply_blur(self, img, area, blur_radius=10):
        x0, y0, x1, y1 = [int(coord) for coord in area['rect']]
        
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle([x0, y0, x1, y1], fill=255)
        
        blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        img.paste(blurred, mask=mask)
        return img

    def upload_to_firebase(self, pdf_bytes, filename, doc_id):
        try:
            blob_path = f"pdfs/{doc_id}/{filename}"
            blob = self.bucket.blob(blob_path)
            
            blob.metadata = {'firebaseStorageDownloadTokens': str(uuid.uuid4())}
            
            blob.upload_from_string(
                pdf_bytes,
                content_type='application/pdf',
                timeout=300
            )
            
            blob.make_public()
            url = blob.generate_signed_url(
                version='v4',
                expiration=604800,
                method='GET'
            )
            
            logger.info(f"Successfully uploaded {filename}")
            return url
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise

    def process_pdf(self, pdf_bytes, original_filename, doc_id, owner_password, user_password, blur_radius=10):
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        original_pdf = BytesIO()
        blurred_pdf = BytesIO()
        sensitive_data = []

        try:
            # Save original version
            pdf_document.save(original_pdf)
            
            # Create blurred version
            with tempfile.TemporaryDirectory() as temp_dir:
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    areas = self.find_sensitive_data(page)
                    
                    if areas:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        for area in areas:
                            area['rect'] = [coord * 2 for coord in area['rect']]
                            img = self.apply_blur(img, area, blur_radius)
                            sensitive_data.append({
                                'page': page_num + 1,
                                'type': area['type']
                            })
                        
                        temp_path = os.path.join(temp_dir, f"page_{page_num}.png")
                        img.save(temp_path, "PNG")
                        page.insert_image(page.rect, filename=temp_path)
                
                pdf_document.save(blurred_pdf)

            # Hash passwords
            owner_password_hash = bcrypt.hashpw(owner_password.encode(), bcrypt.gensalt()).decode()
            user_password_hash = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt()).decode()

            # Upload to Firebase
            original_url = self.upload_to_firebase(
                original_pdf.getvalue(), 
                f"original_{original_filename}", 
                doc_id
            )
            blurred_url = self.upload_to_firebase(
                blurred_pdf.getvalue(), 
                f"blurred_{original_filename}", 
                doc_id
            )

            # Store document info
            doc_ref = self.db.collection('documents').document(doc_id)
            doc_ref.set({
                'filename': original_filename,
                'owner_password': owner_password_hash,
                'user_password': user_password_hash,
                'original_url': original_url,
                'blurred_url': blurred_url,
                'sensitive_data': sensitive_data,
                'created_at': datetime.now(),
                'access_count': 0
            })

            return doc_id
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
        finally:
            pdf_document.close()

def main():
    st.set_page_config(page_title="PDF Processor - Upload & Process", layout="wide")
    st.title("PDF Sensitive Data Masker - Upload")
    
    try:
        masker = PDFMasker()
        st.success("✅ Connected to Firebase successfully")
    except Exception as e:
        st.error(f"❌ Failed to connect to Firebase: {str(e)}")
        st.stop()
    
    st.write("Upload a PDF to create protected versions with masked sensitive information.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            custom_doc_id = st.text_input("Enter Document ID", 
                                        help="Enter a unique identifier for your document")
            owner_password = st.text_input("Set Owner Password", type="password", 
                                         help="Password for accessing original content")
        with col2:
            user_password = st.text_input("Set User Password", type="password",
                                        help="Password for accessing blurred content")
        
        blur_radius = st.slider("Blur Intensity", 5, 20, 10,
                              help="Adjust the blur effect intensity")
        
        if st.button("Process PDF"):
            if not custom_doc_id or not owner_password or not user_password:
                st.error("Please fill in all fields (Document ID and passwords)")
                return
            
            if owner_password == user_password:
                st.error("Owner and user passwords must be different")
                return
            
            try:
                # Check if document ID already exists
                if masker.check_doc_id_exists(custom_doc_id):
                    st.error("This Document ID already exists. Please choose a different one.")
                    return
                
                with st.spinner("Processing PDF..."):
                    doc_id = masker.process_pdf(
                        uploaded_file.getvalue(),
                        uploaded_file.name,
                        custom_doc_id,
                        owner_password,
                        user_password,
                        blur_radius
                    )
                    
                    st.success("✅ PDF processed successfully!")
                    st.info(f"""
                    Your document ID: {doc_id}
                    Please save this ID and your passwords to access the document later.
                    """)
                    
            except Exception as e:
                st.error(f"❌ Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main()