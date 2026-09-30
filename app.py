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
st.divider()

st.subheader("➕ Pridať ponuku")

with st.form("add_offer_form"):
    offer_type = st.selectbox(
        "Typ ponuky",
        ["Darujem", "Vymením", "Ponúkam pomoc"]
    )

    title = st.text_input("Názov ponuky")

    description = st.text_area("Popis")

    name = st.text_input("Meno alebo prezývka")

    contact = st.text_input("Kontakt")

    submitted = st.form_submit_button("Odoslať ponuku")

    if submitted:
        if not title or not description or not name or not contact:
            st.warning("Prosím, vyplň všetky povinné údaje.")
        else:
            new_offer = {
                "Type": offer_type,
                "Title": title,
                "Description": description,
                "Name": name,
                "Contact": contact,
                "Status": "pending"
            }

            supabase.table("Offers").insert(new_offer).execute()

            st.success(
                "Ďakujeme. Ponuka bola odoslaná a zobrazí sa po schválení."
            )
