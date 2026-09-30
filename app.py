import streamlit as st
from supabase import create_client
from PIL import Image
from io import BytesIO
import uuid
import hashlib
import hmac
import secrets


# =========================================================
# NASTAVENIE APLIKÁCIE
# =========================================================

st.set_page_config(
    page_title="Rastislavice zdieľajú",
    page_icon="🌱",
    layout="centered"
)


# =========================================================
# VLASTNÝ DIZAJN
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #e5d6c2;
        color: #7b3f06;
    }

    html, body, [class*="css"] {
        color: #7b3f06;
    }

    h1, h2, h3, h4, h5, h6, p, label, div, span {
        color: #7b3f06 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #e5d6c2;
    }

    div[data-testid="stExpander"] {
        background-color: #f3e8d8;
        border: 1px solid #d2b48c;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 600;
        color: #7b3f06 !important;
    }

    div[data-testid="stForm"] {
        background-color: #f3e8d8;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #d2b48c;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stFileUploader {
        background-color: #fffaf5 !important;
        color: #7b3f06 !important;
        border-radius: 8px;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background-color: #b8834f !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background-color: #9c6d40 !important;
        color: white !important;
    }

    div[data-testid="stCaptionContainer"] p {
        color: #8a5a2b !important;
    }

    hr {
        border-color: #d2b48c;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# PRIPOJENIE NA SUPABASE
# =========================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

admin_supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SECRET_KEY"]
)


# =========================================================
# FUNKCIE PRE PIN
# =========================================================

def create_pin_hash(pin):
    salt = secrets.token_hex(16)

    secret_key = st.secrets["SUPABASE_SECRET_KEY"]

    pin_hash = hmac.new(
        secret_key.encode(),
        f"{salt}:{pin}".encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{salt}:{pin_hash}"


def verify_pin(pin, stored_value):
    if not stored_value:
        return False

    try:
        salt, stored_hash = stored_value.split(":", 1)

        secret_key = st.secrets["SUPABASE_SECRET_KEY"]

        calculated_hash = hmac.new(
            secret_key.encode(),
            f"{salt}:{pin}".encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(
            calculated_hash,
            stored_hash
        )

    except Exception:
        return False


# =========================================================
# POMOCNÁ FUNKCIA NA VYMAZANIE FOTOGRAFIE
# =========================================================

def delete_photo(photo_url):
    if not photo_url:
        return

    try:
        file_name = photo_url.split("/")[-1]

        admin_supabase.storage.from_(
            "offer-images"
        ).remove(
            [file_name]
        )

    except Exception:
        pass


# =========================================================
# HLAVIČKA
# =========================================================

# AK BUDEŠ MAŤ LOGO, ODKOMENTUJ NASLEDUJÚCI RIADOK
# a nahraj si súbor napríklad do GitHub repozitára ako logo.png
# st.image("logo.png", width=140)

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


public_columns = (
    "id,"
    "created_at,"
    "Type,"
    "Title,"
    "Description,"
    "Name,"
    "Contact,"
    "photo_url,"
    "Status"
)


query = (
    supabase
    .table("Offers")
    .select(public_columns)
    .eq("Status", "approved")
    .order("created_at", desc=True)
)


if selected_type != "Všetky":
    query = query.eq(
        "Type",
        selected_type
    )


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

        offer_type = offer.get(
            "Type",
            ""
        )

        title = offer.get(
            "Title",
            "Bez názvu"
        )


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


            st.markdown(
                "**Popis**"
            )

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


            # =================================================
            # VYMAZANIE VLASTNEJ PONUKY
            # =================================================

            with st.expander(
                "🗑️ Moja ponuka – odstrániť",
                expanded=False
            ):

                st.caption(
                    "Zadajte 6-miestny PIN, "
                    "ktorý ste zadali pri vytváraní ponuky."
                )


                delete_pin = st.text_input(
                    "PIN",
                    type="password",
                    max_chars=6,
                    key=f"delete_pin_{offer['id']}"
                )


                attempts_key = (
                    f"delete_attempts_{offer['id']}"
                )


                if attempts_key not in st.session_state:
                    st.session_state[
                        attempts_key
                    ] = 0


                if st.button(
                    "Vymazať moju ponuku",
                    key=f"delete_offer_{offer['id']}"
                ):

                    if (
                        not delete_pin.isdigit()
                        or len(delete_pin) != 6
                    ):

                        st.warning(
                            "PIN musí obsahovať "
                            "presne 6 číslic."
                        )

                    elif (
                        st.session_state[
                            attempts_key
                        ] >= 5
                    ):

                        st.error(
                            "Bolo zadaných príliš veľa "
                            "nesprávnych pokusov. "
                            "Obnovte aplikáciu neskôr."
                        )

                    else:

                        private_response = (
                            admin_supabase
                            .table("Offers")
                            .select(
                                "id,photo_url,delete_pin_hash"
                            )
                            .eq(
                                "id",
                                offer["id"]
                            )
                            .limit(1)
                            .execute()
                        )


                        if not private_response.data:

                            st.error(
                                "Ponuka už neexistuje."
                            )

                        else:

                            private_offer = (
                                private_response.data[0]
                            )


                            if verify_pin(
                                delete_pin,
                                private_offer.get(
                                    "delete_pin_hash"
                                )
                            ):

                                delete_photo(
                                    private_offer.get(
                                        "photo_url"
                                    )
                                )


                                (
                                    admin_supabase
                                    .table("Offers")
                                    .delete()
                                    .eq(
                                        "id",
                                        offer["id"]
                                    )
                                    .execute()
                                )


                                st.success(
                                    "Ponuka bola vymazaná."
                                )

                                st.rerun()

                            else:

                                st.session_state[
                                    attempts_key
                                ] += 1

                                remaining = (
                                    5
                                    - st.session_state[
                                        attempts_key
                                    ]
                                )

                                st.error(
                                    f"Nesprávny PIN. "
                                    f"Zostávajúce pokusy: "
                                    f"{remaining}"
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


        delete_pin = st.text_input(
            "PIN na neskoršie vymazanie ponuky",
            type="password",
            max_chars=6,
            help=(
                "Zvoľte si 6 číslic. "
                "PIN si zapamätajte – "
                "budete ho potrebovať, "
                "ak budete chcieť ponuku vymazať."
            )
        )


        delete_pin_repeat = st.text_input(
            "Zopakujte PIN",
            type="password",
            max_chars=6
        )


        submitted = (
            st.form_submit_button(
                "Odoslať ponuku"
            )
        )


        if submitted:

            title_clean = (
                title.strip()
            )

            description_clean = (
                description.strip()
            )

            name_clean = (
                name.strip()
            )

            contact_clean = (
                contact.strip()
            )


            if (
                not title_clean
                or not description_clean
                or not name_clean
                or not contact_clean
            ):

                st.warning(
                    "Prosím, vyplň všetky povinné údaje."
                )


            elif (
                not delete_pin.isdigit()
                or len(delete_pin) != 6
            ):

                st.warning(
                    "PIN musí obsahovať "
                    "presne 6 číslic."
                )


            elif (
                delete_pin
                != delete_pin_repeat
            ):

                st.warning(
                    "Zadané PIN kódy sa nezhodujú."
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

                        image = image.convert(
                            "RGB"
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
                # HASH PIN-U
                # =========================================

                delete_pin_hash = (
                    create_pin_hash(
                        delete_pin
                    )
                )


                # =========================================
                # ULOŽENIE PONUKY
                # =========================================

                new_offer = {
                    "Type": offer_type,
                    "Title": title_clean,
                    "Description":
                    description_clean,
                    "Name": name_clean,
                    "Contact": contact_clean,
                    "photo_url": photo_url,
                    "Status": "pending",
                    "delete_pin_hash":
                    delete_pin_hash
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

                st.info(
                    "Nezabudnite si svoj 6-miestny PIN. "
                    "Budete ho potrebovať, "
                    "ak budete chcieť ponuku neskôr vymazať."
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


                    with col2:

                        if st.button(
                            "❌ Zamietnuť a vymazať",
                            key=(
                                f"reject_"
                                f"{offer['id']}"
                            )
                        ):

                            delete_photo(
                                offer.get(
                                    "photo_url"
                                )
                            )


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
                            f"admin_delete_"
                            f"{offer['id']}"
                        )
                    ):

                        delete_photo(
                            offer.get(
                                "photo_url"
                            )
                        )


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
