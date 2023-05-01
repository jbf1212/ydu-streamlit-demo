import streamlit as st
from PIL import Image

from ec3 import EC3Materials

ec3_token = st.secrets["EC3_TOKEN"]


def load_mat_data(mat_obj, param_dict, postal_code, plant_dist):
    mat_records = mat_obj.get_materials_within_region(
        postal_code,
        plant_distance=plant_dist,
        params=param_dict,
    )
    return mat_records


def is_valid_postal_code(postal_code):
    if len(postal_code) != 5:
        return False
    try:
        int(postal_code)
        return True
    except ValueError:
        return False

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

######################################
# Make request for material data
######################################
if submitted:
    if not is_valid_postal_code(postal_code):
        st.warning(
            "Invalid postal code. Please enter a 5-digit code with integers only."
        )
        st.stop()
    else:
        postal_int = int(postal_code)

    miles_str = str(miles) + " mi"

    ec3_materials = EC3Materials(bearer_token=ec3_token, ssl_verify=False)

    # Conduct a search of normal weights concrete mixes between min and max strengths
    mat_param_dict = {
        "product_classes": {"EC3": "Concrete >> ReadyMix"},
        "lightweight": weight_type,
        "concrete_compressive_strength_28d": conc_strength_str,
    }

    ec3_materials.return_fields = [
        "id",
        "concrete_compressive_strength_28d",
        "gwp",
        "name",
        "plant_or_group",
    ]

    ec3_materials.max_records = 2500 #limit material records to 2500 for sake of speed
    ec3_materials.only_valid = True #only includes materials from epds that are valid as of the current date

    # NOTE The following query may take a couple minutes to return all responses
    with st.spinner("Searching for materials..."):
        mat_records = load_mat_data(
            ec3_materials, mat_param_dict, postal_int, miles_str
        )

    # Warn user if no records found within radius
    if len(mat_records) == 0:
        st.warning('No material records found within region. Try adjusting distance or other parameters.', icon="⚠️")
        st.stop()

    st.write("{} material records were returned.".format(len(mat_records)))
    st.write(mat_records)