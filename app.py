import streamlit as st
from supabase import create_client
from PIL import Image
from io import BytesIO
import uuid


# =========================================================
# NASTAVENIE APLIKÁCIE
# =========================================================

st.set_page_config(
    page_title="Rastislavice zdieľajú",
    page_icon="🌱",
    layout="centered"
)


# =========================================================
# PRIPOJENIE NA SUPABASE
# =========================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# =========================================================
# HLAVIČKA
# =========================================================

st.title("🌱 Rastislavice zdieľajú")

st.caption(
    "Darovanie, výmena a susedská pomoc na jednom mieste."
)


# =========================================================
# AKTUÁLNE PONUKY
# =========================================================

st.subheader("Aktuálne ponuky")

selected_type = st.selectbox(
    "Filtrovať podľa typu",
    [
        "Všetky",
        "Darujem",
        "Vymením",
        "Ponúkam pomoc"
    ]
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


# =========================================================
# ZOBRAZENIE PONÚK
# =========================================================

if not offers:

    st.info(
        "Momentálne tu nie sú žiadne aktuálne ponuky."
    )

else:

    st.caption(
        f"Počet ponúk: {len(offers)}"
    )

    for offer in offers:

        offer_type = offer.get("Type", "")
        title = offer.get("Title", "Bez názvu")

        if offer_type == "Darujem":
            icon = "🎁"

        elif offer_type == "Vymením":
            icon = "🔄"

        elif offer_type == "Ponúkam pomoc":
            icon = "🤝"

        else:
            icon = "📌"

        expander_title = (
            f"{icon} {offer_type} | {title}"
        )

        with st.expander(
            expander_title,
            expanded=False
        ):

            if offer.get("photo_url"):
                st.image(
                    offer["photo_url"],
                    width=320
                )

            st.markdown("**Popis**")

            st.write(
                offer.get(
                    "Description",
                    ""
                )
            )

            st.markdown(
                f"**Ponúka:** "
                f"{offer.get('Name', '')}"
            )

            st.markdown(
                f"**Kontakt:** "
                f"{offer.get('Contact', '')}"
            )


# =========================================================
# PRIDANIE PONUKY
# =========================================================

st.divider()

with st.expander(
    "➕ Pridať novú ponuku",
    expanded=False
):

    st.caption(
        "Ponuka sa zobrazí až po schválení administrátorom."
    )

    with st.form(
        "add_offer_form"
    ):

        offer_type = st.selectbox(
            "Typ ponuky",
            [
                "Darujem",
                "Vymením",
                "Ponúkam pomoc"
            ]
        )

        title = st.text_input(
            "Názov ponuky",
            max_chars=60,
            help="Maximálne 60 znakov."
        )

        description = st.text_area(
            "Popis",
            max_chars=500,
            help="Maximálne 500 znakov."
        )

        photo = st.file_uploader(
            "Fotografia ponuky",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            help=(
                "Maximálna veľkosť fotografie "
                "je 5 MB."
            )
        )

        name = st.text_input(
            "Meno alebo prezývka",
            max_chars=60
        )

        contact = st.text_input(
            "Kontakt",
            max_chars=100,
            help=(
                "Telefón, e-mail alebo iný kontakt."
            )
        )

        submitted = (
            st.form_submit_button(
                "Odoslať ponuku"
            )
        )


        if submitted:

            title_clean = title.strip()
            description_clean = description.strip()
            name_clean = name.strip()
            contact_clean = contact.strip()

            if (
                not title_clean
                or not description_clean
                or not name_clean
                or not contact_clean
            ):

                st.warning(
                    "Prosím, vyplň všetky povinné údaje."
                )

            else:

                photo_url = None


                # =========================================
                # SPRACOVANIE FOTOGRAFIE
                # =========================================

                if photo is not None:

                    max_file_size = (
                        5 * 1024 * 1024
                    )

                    if (
                        photo.size
                        > max_file_size
                    ):

                        st.error(
                            "Fotografia je príliš veľká. "
                            "Maximálna povolená veľkosť "
                            "je 5 MB."
                        )

                        st.stop()


                    try:

                        image = Image.open(
                            photo
                        )

                        image.verify()

                        photo.seek(0)

                        image = Image.open(
                            photo
                        )

                    except Exception:

                        st.error(
                            "Súbor sa nepodarilo spracovať "
                            "ako obrázok. Nahrajte JPG, "
                            "JPEG alebo PNG."
                        )

                        st.stop()


                    if image.mode != "RGB":

                        image = (
                            image.convert(
                                "RGB"
                            )
                        )


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

                    compressed_image = (
                        buffer.getvalue()
                    )

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
                        .from_(
                            "offer-images"
                        )
                        .get_public_url(
                            file_name
                        )
                    )


                # =========================================
                # ULOŽENIE PONUKY
                # =========================================

                new_offer = {
                    "Type": offer_type,
                    "Title": title_clean,
                    "Description": description_clean,
                    "Name": name_clean,
                    "Contact": contact_clean,
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


# =========================================================
# ADMINISTRÁCIA
# =========================================================

st.divider()

with st.expander(
    "🔐 Administrácia",
    expanded=False
):

    admin_password = st.text_input(
        "Admin heslo",
        type="password"
    )


    if (
        admin_password
        == st.secrets[
            "ADMIN_PASSWORD"
        ]
    ):

        st.success(
            "Admin prístup povolený."
        )

        admin_supabase = (
            create_client(
                st.secrets[
                    "SUPABASE_URL"
                ],
                st.secrets[
                    "SUPABASE_SECRET_KEY"
                ]
            )
        )


        # =================================================
        # ČAKAJÚCE PONUKY
        # =================================================

        st.subheader(
            "⏳ Čakajúce na schválenie"
        )


        pending_response = (
            admin_supabase
            .table("Offers")
            .select("*")
            .eq(
                "Status",
                "pending"
            )
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
                "Žiadne ponuky nečakajú "
                "na schválenie."
            )

        else:

            for offer in pending_offers:

                pending_title = (
                    f"{offer.get('Type', '')} | "
                    f"{offer.get('Title', '')}"
                )

                with st.expander(
                    pending_title,
                    expanded=False
                ):

                    if offer.get(
                        "photo_url"
                    ):

                        st.image(
                            offer[
                                "photo_url"
                            ],
                            width=280
                        )


                    st.write(
                        offer.get(
                            "Description",
                            ""
                        )
                    )

                    st.markdown(
                        f"**Meno:** "
                        f"{offer.get('Name', '')}"
                    )

                    st.markdown(
                        f"**Kontakt:** "
                        f"{offer.get('Contact', '')}"
                    )


                    col1, col2 = (
                        st.columns(2)
                    )


                    # =====================================
                    # SCHVÁLIŤ
                    # =====================================

                    with col1:

                        if st.button(
                            "✅ Schváliť",
                            key=(
                                f"approve_"
                                f"{offer['id']}"
                            )
                        ):

                            (
                                admin_supabase
                                .table(
                                    "Offers"
                                )
                                .update(
                                    {
                                        "Status":
                                        "approved"
                                    }
                                )
                                .eq(
                                    "id",
                                    offer[
                                        "id"
                                    ]
                                )
                                .execute()
                            )

                            st.rerun()


                    # =====================================
                    # ZAMIETNUŤ A VYMAZAŤ
                    # =====================================

                    with col2:

                        if st.button(
                            "❌ Zamietnuť a vymazať",
                            key=(
                                f"reject_"
                                f"{offer['id']}"
                            )
                        ):

                            # Najskôr vymažeme fotografiu

                            if offer.get(
                                "photo_url"
                            ):

                                file_name = (
                                    offer[
                                        "photo_url"
                                    ]
                                    .split("/")[
                                        -1
                                    ]
                                )

                                (
                                    admin_supabase
                                    .storage
                                    .from_(
                                        "offer-images"
                                    )
                                    .remove(
                                        [
                                            file_name
                                        ]
                                    )
                                )

                            # Potom vymažeme celý záznam

                            (
                                admin_supabase
                                .table(
                                    "Offers"
                                )
                                .delete()
                                .eq(
                                    "id",
                                    offer[
                                        "id"
                                    ]
                                )
                                .execute()
                            )

                            st.rerun()


        # =================================================
        # AKTÍVNE PONUKY
        # =================================================

        st.subheader(
            "🟢 Aktívne ponuky"
        )


        active_response = (
            admin_supabase
            .table("Offers")
            .select("*")
            .eq(
                "Status",
                "approved"
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        active_offers = (
            active_response.data
        )


        if not active_offers:

            st.info(
                "Momentálne nie sú "
                "žiadne aktívne ponuky."
            )

        else:

            for offer in active_offers:

                active_title = (
                    f"{offer.get('Type', '')} | "
                    f"{offer.get('Title', '')}"
                )

                with st.expander(
                    active_title,
                    expanded=False
                ):

                    if offer.get(
                        "photo_url"
                    ):

                        st.image(
                            offer[
                                "photo_url"
                            ],
                            width=280
                        )


                    st.write(
                        offer.get(
                            "Description",
                            ""
                        )
                    )


                    st.markdown(
                        f"**Meno:** "
                        f"{offer.get('Name', '')}"
                    )


                    st.markdown(
                        f"**Kontakt:** "
                        f"{offer.get('Contact', '')}"
                    )


                    if st.button(
                        "🗑️ Vymazať ponuku",
                        key=(
                            f"delete_"
                            f"{offer['id']}"
                        )
                    ):

                        # Najskôr odstránime fotografiu

                        if offer.get(
                            "photo_url"
                        ):

                            file_name = (
                                offer[
                                    "photo_url"
                                ]
                                .split("/")[
                                    -1
                                ]
                            )

                            (
                                admin_supabase
                                .storage
                                .from_(
                                    "offer-images"
                                )
                                .remove(
                                    [
                                        file_name
                                    ]
                                )
                            )


                        # Potom odstránime záznam
                        # z databázy

                        (
                            admin_supabase
                            .table(
                                "Offers"
                            )
                            .delete()
                            .eq(
                                "id",
                                offer[
                                    "id"
                                ]
                            )
                            .execute()
                        )

                        st.rerun()


    elif admin_password:

        st.error(
            "Nesprávne admin heslo."
        )
