import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import io
import zipfile

# --- Page Config ---
st.set_page_config(page_title="Xizoa PDF Cleaner", page_icon="✂️")
st.title("✂️ PDF Logo Remover")
st.write("Upload PDF → Remove Top Logo → Download Images")

# --- Sidebar Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    crop_pixels = st.slider("Upar se kitna kaatna hai? (Pixels)", 0, 300, 80)
    dpi = st.select_slider("Image Quality (DPI)", options=[72, 100, 150, 200], value=150)
    img_format = st.selectbox("Image Format", ["PNG", "JPEG"], index=0)
    
    st.info("💡 **Tip:** DPI kam karo agar file size badi ban rahi hai")

# --- Upload ---
uploaded_file = st.file_uploader("Apna PDF yahan daalo", type=["pdf"])

if uploaded_file is not None:
    # File size check (50MB limit)
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    
    if file_size_mb > 50:
        st.error(f"❌ PDF bahut badi hai ({file_size_mb:.1f} MB). Max 50MB allowed.")
        st.stop()
    
    st.info(f"📄 Processing PDF ({file_size_mb:.1f} MB)... Thoda time lagega.")
    
    try:
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # PDF ko Images me convert (low memory mode)
        status_text.text("Step 1/3: PDF read ho raha hai...")
        images = convert_from_bytes(
            uploaded_file.read(), 
            dpi=dpi,  # Quality control
            fmt=img_format.lower()
        )
        progress_bar.progress(33)
        
        total_pages = len(images)
        st.success(f"✅ {total_pages} pages mili!")
        
        # Preview + Cropping
        status_text.text(f"Step 2/3: {total_pages} images crop ho rahi hain...")
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Preview: Pehli aur aakhri image
            col1, col2 = st.columns(2)
            
            for i, img in enumerate(images):
                width, height = img.size
                
                # Safety: Agar crop value image se badi hai
                safe_crop = min(crop_pixels, height - 100)
                
                # Crop karo
                crop_box = (0, safe_crop, width, height)
                cleaned_img = img.crop(crop_box)
                
                # Preview (pehli aur aakhri)
                if i == 0:
                    with col1:
                        st.write("**📄 Page 1 (Before)**")
                        st.image(img, use_column_width=True)
                        st.write("**✂️ Page 1 (After)**")
                        st.image(cleaned_img, use_column_width=True)
                
                if i == total_pages - 1 and total_pages > 1:
                    with col2:
                        st.write(f"**📄 Page {total_pages} (Before)**")
                        st.image(img, use_column_width=True)
                        st.write(f"**✂️ Page {total_pages} (After)**")
                        st.image(cleaned_img, use_column_width=True)
                
                # Save to ZIP
                img_byte_arr = io.BytesIO()
                
                if img_format == "JPEG":
                    # JPEG me transparency nahi hoti, white background add karo
                    cleaned_img = cleaned_img.convert("RGB")
                    cleaned_img.save(img_byte_arr, format='JPEG', quality=85)
                else:
                    cleaned_img.save(img_byte_arr, format='PNG', optimize=True)
                
                file_ext = "jpg" if img_format == "JPEG" else "png"
                zip_file.writestr(f"slide_{i+1:03d}.{file_ext}", img_byte_arr.getvalue())
                
                # Progress update
                progress = int(33 + (i+1)/total_pages * 33)
                progress_bar.progress(progress)
        
        progress_bar.progress(100)
        status_text.text("Step 3/3: ZIP file ready!")
        
        # Final Stats
        zip_size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)
        
        st.success(f"🎉 **Taiyaar hai!**")
        st.metric("Total Pages", total_pages)
        st.metric("ZIP Size", f"{zip_size_mb:.2f} MB")
        st.metric("Cropped Pixels", f"{safe_crop}px")
        
        # Download
        st.download_button(
            label="📥 Download Cleaned Images (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"xizoa_cleaned_{total_pages}pages.zip",
            mime="application/zip",
            type="primary"
        )
        
    except Exception as e:
        st.error(f"❌ Error aaya: {e}")
        st.write("**Possible reasons:**")
        st.write("- PDF corrupted hai")
        st.write("- Poppler installed nahi hai (system dependency)")
        st.write("- PDF password-protected hai")

else:
    # Instructions
    st.write("### 📖 Kaise Use Karein?")
    st.write("1. ⬆️ PDF upload karo")
    st.write("2. 🎚️ Sidebar se crop size adjust karo")
    st.write("3. 📥 ZIP download karo")
    
    st.warning("⚠️ **Note:** Poppler install hona chaiye system pe (`apt install poppler-utils` Linux/Mac)")
