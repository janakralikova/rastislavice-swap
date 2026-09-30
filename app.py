import streamlit as st
from supabase import create_client
from PIL import Image
from io import BytesIO
import uuid


st.set_page_config(
    page_title="Rastislavice zdieľajú",
    page_icon="🌱",
    layout="centered"
)


# -----------------------------
# PRIPOJENIE NA SUPABASE
# -----------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# -----------------------------
# HLAVIČKA
# -----------------------------

st.title("🌱 Rastislavice zdieľajú")

st.write(
    "Miesto, kde môžeme darovať, vymeniť alebo ponúknuť pomoc."
)


# -----------------------------
# AKTUÁLNE PONUKY
# -----------------------------

st.subheader("Aktuálne ponuky")

selected_type = st.selectbox(
    "Filtrovať ponuky",
    ["Všetky", "Darujem", "Vymením", "Ponúkam pomoc"]
)

query = (
    supabase
    .table("Offers")
    .select("*")
    .eq("Status", "approved")
    .order("created_at", desc=True)
)

if selected_type != "Všetky":
    query = query.eq("Type", selected_type)

response = query.execute()

offers = response.data


if not offers:
    st.info("Momentálne tu nie sú žiadne ponuky.")

else:
    for offer in offers:

        st.markdown(f"### {offer['Title']}")

        if offer.get("photo_url"):
            st.image(
                offer["photo_url"],
                use_container_width=True
            )

        st.write(f"**Typ:** {offer['Type']}")

        st.write(offer["Description"])

        st.write(f"**Ponúka:** {offer['Name']}")

        st.write(f"**Kontakt:** {offer['Contact']}")

        st.divider()


# -----------------------------
# PRIDANIE NOVEJ PONUKY
# -----------------------------

st.subheader("➕ Pridať ponuku")

with st.form("add_offer_form"):

    offer_type = st.selectbox(
        "Typ ponuky",
        [
            "Darujem",
            "Vymením",
            "Ponúkam pomoc"
        ]
    )

    title = st.text_input(
        "Názov ponuky"
    )

    description = st.text_area(
        "Popis"
    )

    photo = st.file_uploader(
        "Fotografia ponuky",
        type=["jpg", "jpeg", "png"]
    )

    name = st.text_input(
        "Meno alebo prezývka"
    )

    contact = st.text_input(
        "Kontakt"
    )

    submitted = st.form_submit_button(
        "Odoslať ponuku"
    )


    if submitted:

        if not title or not description or not name or not contact:

            st.warning(
                "Prosím, vyplň všetky povinné údaje."
            )

        else:

            photo_url = None


            # -----------------------------
            # SPRACOVANIE FOTOGRAFIE
            # -----------------------------

            if photo is not None:

                image = Image.open(photo)

                if image.mode != "RGB":
                    image = image.convert("RGB")

                image.thumbnail(
                    (1000, 1000)
                )

                buffer = BytesIO()

                image.save(
                    buffer,
                    format="JPEG",
                    quality=75,
                    optimize=True
                )

                compressed_image = buffer.getvalue()

                file_name = (
                    f"{uuid.uuid4()}.jpg"
                )

                supabase.storage.from_(
                    "offer-images"
                ).upload(
                    file_name,
                    compressed_image,
                    {
                        "content-type":
                        "image/jpeg"
                    }
                )

                photo_url = (
                    supabase
                    .storage
                    .from_("offer-images")
                    .get_public_url(
                        file_name
                    )
                )


            # -----------------------------
            # ULOŽENIE PONUKY
            # -----------------------------

            new_offer = {
                "Type": offer_type,
                "Title": title,
                "Description": description,
                "Name": name,
                "Contact": contact,
                "photo_url": photo_url,
                "Status": "pending"
            }

            supabase.table(
                "Offers"
            ).insert(
                new_offer,
                returning="minimal"
            ).execute()

            st.success(
                "Ďakujeme. Ponuka bola odoslaná "
                "a zobrazí sa po schválení."
            )


# -----------------------------
# ADMINISTRÁCIA
# -----------------------------

st.divider()

with st.expander("🔐 Administrácia"):

    admin_password = st.text_input(
        "Admin heslo",
        type="password"
    )

    if admin_password == st.secrets["ADMIN_PASSWORD"]:

        st.success(
            "Admin prístup povolený."
        )

        admin_supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SECRET_KEY"]
        )

        pending_response = (
            admin_supabase
            .table("Offers")
            .select("*")
            .eq("Status", "pending")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        pending_offers = (
            pending_response.data
        )


        if not pending_offers:

            st.info(
                "Momentálne nie sú žiadne "
                "ponuky na schválenie."
            )

        else:

            st.subheader(
                "Ponuky čakajúce na schválenie"
            )

            for offer in pending_offers:

                st.markdown(
                    f"### {offer['Title']}"
                )

                if offer.get("photo_url"):
                    st.image(
                        offer["photo_url"],
                        use_container_width=True
                    )

                st.write(
                    f"**Typ:** {offer['Type']}"
                )

                st.write(
                    offer["Description"]
                )

                st.write(
                    f"**Meno:** {offer['Name']}"
                )

                st.write(
                    f"**Kontakt:** {offer['Contact']}"
                )

                col1, col2 = st.columns(2)


                with col1:

                    if st.button(
                        "✅ Schváliť",
                        key=f"approve_{offer['id']}"
                    ):

                        (
                            admin_supabase
                            .table("Offers")
                            .update(
                                {
                                    "Status":
                                    "approved"
                                }
                            )
                            .eq(
                                "id",
                                offer["id"]
                            )
                            .execute()
                        )

                        st.success(
                            "Ponuka bola schválená."
                        )

                        st.rerun()


                with col2:

                    if st.button(
        "❌ Zamietnuť",
        key=f"reject_{offer['id']}"
    ):

        if offer.get("photo_url"):

            file_name = offer["photo_url"].split("/")[-1]

            admin_supabase.storage.from_(
                "offer-images"
            ).remove(
                [file_name]
            )

        (
            admin_supabase
            .table("Offers")
            .update(
                {
                    "Status": "rejected",
                    "photo_url": None
                }
            )
            .eq(
                "id",
                offer["id"]
            )
            .execute()
        )

        st.warning(
            "Ponuka bola zamietnutá."
        )

        st.rerun()

                        (
                            admin_supabase
                            .table("Offers")
                            .update(
                                {
                                    "Status":
                                    "rejected"
                                }
                            )
                            .eq(
                                "id",
                                offer["id"]
                            )
                            .execute()
                        )

                        st.warning(
                            "Ponuka bola zamietnutá."
                        )

                        st.rerun()


                st.divider()
