import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="Vertex AI Virtual Try-On", layout="wide")
st.title("👕 Vertex AI Virtual Try-On Explorer")

# --- Sidebar: Configuration ---
with st.sidebar:
    st.header("1. API Configuration")
    project_id = st.text_input("Google Project ID", placeholder="your-project-id")
    # UPDATED: Changed default to us-central1 for model availability
    location = st.text_input("Google Region", value="us-central1")
    
    st.divider()
    st.header("2. Parameters")
    num_images = st.slider("Images to generate", min_value=1, max_value=4, value=1)
    
    mime_type_toggle = st.radio("Output Format", ["image/png", "image/jpeg"])
    
    is_jpeg = mime_type_toggle == "image/jpeg"
    compression_level = st.slider(
        "JPEG Compression", 
        min_value=0, 
        max_value=100, 
        value=75, 
        disabled=not is_jpeg
    )

# --- Main UI Layout ---
input_col, output_col = st.columns([1, 1], gap="large")

with input_col:
    st.header("📥 Input Assets")
    person_file = st.file_uploader("Upload Person Image", type=['jpg', 'jpeg', 'png'])
    cloth_file = st.file_uploader("Upload Clothing Image", type=['jpg', 'jpeg', 'png'])
    
    if person_file: st.image(person_file, caption="Target Person", width=250)
    if cloth_file: st.image(cloth_file, caption="Clothing Item", width=250)
    
    generate_btn = st.button("Generate Try-On", type="primary", use_container_width=True)

# --- Results Pane ---
with output_col:
    st.header("✨ Generated Result")
    if generate_btn:
        if not project_id or not person_file or not cloth_file:
            st.error("Please provide Project ID and upload both images.")
        else:
            try:
                with st.spinner("Generating Try-On..."):
                    client = genai.Client(vertexai=True, project=project_id, location=location)
                    
                    # 1. Correct Model ID for 2026 GA
                    model_id = 'virtual-try-on-exp'

                    # 2. Re-verifying the Config Keys for the current SDK
                    vto_config = types.RecontextImageConfig(
                        number_of_images=num_images,
                        output_mime_type=mime_type_toggle,
                        output_compression_quality=compression_level if is_jpeg else None
                    )

                    response = client.models.recontext_image(
                        model=model_id,
                        source=types.RecontextImageSource(
                            person_image=Image.open(person_file),
                            product_images=[
                                types.ProductImage(product_image=Image.open(cloth_file))
                            ]
                        ),
                        config=vto_config
                    )

                    if response.generated_images:
                        for idx, gen_img in enumerate(response.generated_images):
                            st.image(gen_img.image, caption=f"Result {idx+1}", use_container_width=True)
                            
                            ext = "jpg" if is_jpeg else "png"
                            st.download_button(
                                label=f"Download Result {idx+1}",
                                data=gen_img.image,
                                file_name=f"vto_output_{idx+1}.{ext}",
                                mime=mime_type_toggle,
                                key=f"dl_{idx}"
                            )
                    else:
                        st.warning("Request successful, but no images were generated. Try different input photos.")
            except Exception as e:
                # This will catch if the specific 'number_of_images' key still causes a local SDK mismatch
                st.error(f"API Error: {e}")
                st.info("Tip: If you see a 'validation error', the SDK might need to be updated: pip install --upgrade google-genai")
    else:
        st.info("Upload images and click 'Generate'. Result will appear in this pane.")