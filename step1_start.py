import streamlit as st
from PIL import Image

col1, col2, col3 = st.columns(3)
image = Image.open("./images/yourdesk_logo.png")
col2.image(image, width=250)

st.title("YourDesk University Demo App")
st.markdown(
    "**Hi Yourdesk!**"
)

button1 = st.button("Click Me")
if button1:
    st.write("You clicked me!")