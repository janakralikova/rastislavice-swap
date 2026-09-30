import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Rastislavice zdieľajú",
    page_icon="🌱",
    layout="centered"
)

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.title("🌱 Rastislavice zdieľajú")
st.write("Miesto, kde môžeme darovať, vymeniť alebo ponúknuť pomoc.")

st.subheader("Aktuálne ponuky")

response = (
    supabase
    .table("Offers")
    .select("*")
    .eq("Status", "approved")
    .execute()
)

offers = response.data

if not offers:
    st.info("Momentálne tu nie sú žiadne ponuky.")
else:
    for offer in offers:
        st.markdown(f"### {offer['Title']}")
        st.write(f"**Typ:** {offer['Type']}")
        st.write(offer["Description"])
        st.write(f"**Ponúka:** {offer['Name']}")
        st.write(f"**Kontakt:** {offer['Contact']}")
        st.divider()
