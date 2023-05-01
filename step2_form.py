import streamlit as st
from PIL import Image


######################################
# App title and description
######################################
col1, col2, col3 = st.columns(3)
image = Image.open("./images/yourdesk_logo.png")
col2.image(image, width=250)

st.title("YourDesk University Demo App")
st.title("_EC3 Concrete Lookup_")
st.markdown(
    "**Analyze GWP values of concretes within certain proximity to US postal code**"
)

######################################
# Have user enter data
######################################
with st.form(key="concrete_query"):
    with st.sidebar.form(key="Form1"):
        postal_code = st.text_input("Enter a 5-digit postal code")
        miles = st.number_input(
            "Miles from region provided", min_value=0, max_value=500, value=20, step=10
        )
        conc_strength = st.slider(
            label="Set your concrete strength at 28 days (psi)",
            min_value=0,
            max_value=12000,
            value=5000,
            step=100,
        )
        weight_type = st.checkbox("Lightweight")

        submitted = st.form_submit_button(label="Search Concrete Materials 🔎")

conc_strength_str = str(conc_strength) + " psi"

if submitted:
    st.write(postal_code)
    st.write(miles)
    st.write(conc_strength_str)
