import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
import pydeck as pdk

from ec3 import EC3Materials

ec3_token = st.secrets["EC3_TOKEN"]

# NOTE Not caching since I want data to refresh when user resubmits query
def load_mat_data(mat_obj, param_dict, postal_code, plant_dist):
    mat_records = mat_obj.get_materials_within_region(
        postal_code,
        plant_distance=plant_dist,
        params=param_dict,
    )
    return mat_records


def remove_outliers(df, n_std, col_names):
    """
    Remove extreme outliers that are more than n_std standard deviations away from mean
    """
    for col in df[col_names]:
        mean = df[col].mean()
        sd = df[col].std()

        df = df[(df[col] <= mean + (n_std * sd))]

    return df


def is_valid_postal_code(postal_code):
    if len(postal_code) != 5:
        return False
    try:
        int(postal_code)
        return True
    except ValueError:
        return False


def convert_record(rec):
    '''
    The following code will convert all the compressive strengths to the same units and round to the nearest 500 psi
    '''
    new_dict = {}
    split_strength = rec["concrete_compressive_strength_28d"].split()
    if split_strength[1] == "MPa":
        conc_strength = float(split_strength[0]) * 145.03773773 # convert mpa to psi
    elif split_strength[1] == "psi":
        conc_strength = float(split_strength[0])
    elif split_strength[1] == "ksi":
        conc_strength = float(split_strength[0]) * 1000
    else:
        return # unknown unit

    rounded_strength = int(round(conc_strength / 500.0) * 500.0)

    plant_owner_name = rec["plant_or_group"]["owned_by"]["name"]
    plant_local_name = rec["plant_or_group"]["name"]

    if not plant_owner_name:
        plant_owner_name = "Unknown"
    elif not isinstance(plant_owner_name, str):
        plant_owner_name = "Unknown"

    if not plant_local_name:
        plant_local_name = "Unknown"
    elif not isinstance(plant_local_name, str):
        plant_local_name = "Unknown"

    plant_lat = rec["plant_or_group"]["latitude"]
    plant_long = rec["plant_or_group"]["longitude"]

    new_dict["Compressive Strength [psi]"] = rounded_strength
    new_dict["GWP [kgCO2e]"] = float(rec["gwp"].split()[0])
    new_dict["Plant_Owner"] = plant_owner_name
    new_dict["Plant_Name"] = plant_local_name
    new_dict["Product Name"] = rec["name"]
    new_dict["Latitude"] = plant_lat
    new_dict["Longitude"] = plant_long

    return new_dict


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
        st.markdown(
            "This app is a demonstration of using the ec3-python-wrapper for querying the EC3 database."
        )

        link = f'<a href="https://github.com/jbf1212/ec3-python-wrapper" style="color:#4A987F;">Link to ec3-python-wrapper repo</a>'
        st.markdown(link, unsafe_allow_html=True)
        st.markdown("***")

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
        st.markdown(
            '<span style="color:#094D6C;"> Note! Queries may take several minutes to run depending on the number of materials being returned. Max returned set to 2500.</span>',
            unsafe_allow_html=True,
        )

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

    ######################################
    # Clean and convert the data
    ######################################
    converted_records = [convert_record(rec) for rec in mat_records if rec is not None]

    df = pd.DataFrame(converted_records)
    data_length_prior = len(df.index)
    df = remove_outliers(df, 3, ["GWP [kgCO2e]"])
    data_length_post = len(df.index)

    st.markdown("***")
    st.write("{} materials included in filtered data".format(data_length_post))
    st.write("{} materials were deemed to be outliers".format(data_length_prior - data_length_post))

    ######################################
    ## Create simple box plot
    ######################################
    fig = px.box(
        df,
        x="Compressive Strength [psi]",
        y="GWP [kgCO2e]",
        color_discrete_sequence = ["#5051A3"],
        hover_data=["Product Name", "Plant_Owner", "Plant_Name"],
        points="all"
    )
    st.plotly_chart(fig, theme="streamlit")

    st.markdown("***")

    ######################################
    ## Create map plot
    ######################################
    map_df = (
        df.groupby(["Plant_Owner", "Plant_Name", "Latitude", "Longitude"])["Plant_Name"]
        .count()
        .reset_index(name="EPD_Count")
    )

    # Define a layer to display on a map
    mix_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        pickable=True,
        opacity=0.3,
        stroked=True,
        filled=True,
        radius_scale=10,
        radius_min_pixels=5,
        radius_max_pixels=60,
        line_width_min_pixels=1,
        get_position=["Longitude", "Latitude"],
        get_radius="EPD_Count",
        get_fill_color=[80, 81, 163],
        get_line_color=[9, 77, 108],
    )

    # Set view state
    # view_state = pdk.data_utils.compute_view(points=map_df[["Latitude", "Longitude"]], view_proportion=0.9) #This should work, but is not
    mean_lat = map_df.loc[:, "Latitude"].mean()
    mean_long = map_df.loc[:, "Longitude"].mean()
    view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_long, zoom=8)

    # Render map
    r = pdk.Deck(
        layers=[mix_layer],
        initial_view_state=view_state,
        tooltip={"text": "{Plant_Owner}\n{Plant_Name}\nEPD Count: {EPD_Count}"},
        map_style="mapbox://styles/mapbox/light-v10",
    )

    mix_map = st.pydeck_chart(r)