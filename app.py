import streamlit as st
from supabase import create_client
from PIL import Image, ImageChops
from io import BytesIO
from pathlib import Path

import uuid
import hashlib
import hmac
import secrets
import base64


# =========================================================
# NASTAVENIE APLIKÁCIE
# =========================================================

st.set_page_config(
    page_title="Rastislavice zdieľajú",
    page_icon="🌿",
    layout="centered"
)


# =========================================================
# FARBY
# =========================================================

BACKGROUND = "#e5d6c2"
BROWN = "#7b3f06"
LIGHT_BOX = "#f3e8da"
LIGHTER_BOX = "#fffaf4"
BORDER = "#ccb18f"
BUTTON = "#9b6535"
BUTTON_HOVER = "#7b3f06"


# =========================================================
# DIZAJN
# =========================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background-color: {BACKGROUND};
    }}

    .block-container {{
        max-width: 760px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }}

    h1, h2, h3, h4, h5, h6,
    p, label {{
        color: {BROWN};
    }}

    /* HEADER */

    .custom-header {{
        background-color: {LIGHT_BOX};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 14px 16px 16px 16px;
        margin-bottom: 16px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(80, 45, 10, 0.06);
    }}

    .custom-header-logo {{
        width: 105px;
        max-width: 32%;
        margin: 0 auto 4px auto;
        display: block;
    }}

    .custom-header-title {{
        color: {BROWN};
        font-size: 27px;
        font-weight: 700;
        line-height: 1.15;
        margin-top: 2px;
    }}

    .custom-header-subtitle {{
        color: {BROWN};
        font-size: 14px;
        opacity: 0.82;
        margin-top: 5px;
    }}

    /* NADPISY SEKCII */

    .section-title {{
        color: {BROWN};
        font-size: 22px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
    }}

    /* EXPANDERY */

    div[data-testid="stExpander"] {{
        background-color: {LIGHT_BOX};
        border: 1px solid {BORDER};
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 9px;
    }}

    div[data-testid="stExpander"] summary {{
        color: {BROWN} !important;
        font-weight: 650;
    }}

    div[data-testid="stExpander"] summary p {{
        color: {BROWN} !important;
        font-weight: 650;
    }}

    /* FORMULÁRE */

    div[data-testid="stForm"] {{
        background-color: {LIGHTER_BOX};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px;
    }}

    input,
    textarea {{
        background-color: #fffdf9 !important;
        color: {BROWN} !important;
        border-radius: 9px !important;
    }}

    input::placeholder,
    textarea::placeholder {{
        color: #a27d5b !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #fffdf9 !important;
        color: {BROWN} !important;
        border-radius: 9px !important;
    }}

    /* TLAČIDLÁ */

    .stButton > button,
    .stFormSubmitButton > button {{
        background-color: {BUTTON} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 650 !important;
        min-height: 42px;
    }}

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {{
        background-color: {BUTTON_HOVER} !important;
        color: white !important;
    }}

    /* FOTOGRAFIE */

    div[data-testid="stImage"] img {{
        border-radius: 12px;
    }}

    /* CAPTION */

    div[data-testid="stCaptionContainer"] p {{
        color: {BROWN} !important;
        opacity: 0.75;
    }}

    hr {{
        border-color: {BORDER};
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SUPABASE
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
# POMOCNÉ FUNKCIE
# =========================================================

def create_pin_hash(pin):

    salt = secrets.token_hex(16)

    secret_key = st.secrets[
        "SUPABASE_SECRET_KEY"
    ]

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

        salt, stored_hash = stored_value.split(
            ":",
            1
        )

        secret_key = st.secrets[
            "SUPABASE_SECRET_KEY"
        ]

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


def prepare_logo_base64(path):

    image = Image.open(path).convert("RGBA")

    # biele pozadie použijeme ako referenciu
    background = Image.new(
        "RGBA",
        image.size,
        (255, 255, 255, 255)
    )

    diff = ImageChops.difference(
        image,
        background
    )

    bbox = diff.getbbox()

    if bbox:
        image = image.crop(bbox)

    # jemný vnútorný okraj
    padding = 20

    padded = Image.new(
        "RGBA",
        (
            image.width + padding * 2,
            image.height + padding * 2
        ),
        (255, 255, 255, 0)
    )

    padded.paste(
        image,
        (padding, padding),
        image
    )

    buffer = BytesIO()

    padded.save(
        buffer,
        format="PNG"
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode()


# =========================================================
# HEADER S LOGOM
# =========================================================

logo_path = Path("logo.png")

if logo_path.exists():

    logo_base64 = prepare_logo_base64(
        logo_path
    )

    st.markdown(
        f"""
        <div class="custom-header">

            <img
                class="custom-header-logo"
                src="data:image/png;base64,{logo_base64}"
            >

            <div class="custom-header-title">
                Rastislavice zdieľajú
            </div>

            <div class="custom-header-subtitle">
                Darovanie • výmena • susedská pomoc
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        """
        <div class="custom-header">

            <div class="custom-header-title">
                Rastislavice zdieľajú
            </div>

            <div class="custom-header-subtitle">
                Darovanie • výmena • susedská pomoc
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# PRIDAŤ NOVÚ PONUKU
# =========================================================

with st.expander(
    "＋  PRIDAŤ NOVÚ PONUKU",
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
                "Fotografia je nepovinná. "
                "Maximálna veľkosť je 5 MB."
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
                "PIN budete potrebovať "
                "pri neskoršom vymazaní ponuky."
            )
        )

        delete_pin_repeat = st.text_input(
            "Zopakujte PIN",
            type="password",
            max_chars=6
        )

        submitted = st.form_submit_button(
            "Odoslať ponuku"
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


            elif (
                not delete_pin.isdigit()
                or len(delete_pin) != 6
            ):

                st.warning(
                    "PIN musí obsahovať presne 6 číslic."
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


                # -----------------------------------------
                # FOTOGRAFIA
                # -----------------------------------------

                if photo is not None:

                    max_file_size = (
                        5 * 1024 * 1024
                    )

                    if photo.size > max_file_size:

                        st.error(
                            "Fotografia je príliš veľká. "
                            "Maximálna veľkosť je 5 MB."
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
                            "Súbor sa nepodarilo "
                            "spracovať ako obrázok."
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


                delete_pin_hash = create_pin_hash(
                    delete_pin
                )


                new_offer = {

                    "Type":
                    offer_type,

                    "Title":
                    title_clean,

                    "Description":
                    description_clean,

                    "Name":
                    name_clean,

                    "Contact":
                    contact_clean,

                    "photo_url":
                    photo_url,

                    "Status":
                    "pending",

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
                    "Ponuka bola odoslaná "
                    "na schválenie."
                )

                st.info(
                    "Zapamätajte si svoj 6-miestny PIN."
                )


# =========================================================
# AKTUÁLNE PONUKY
# =========================================================

st.markdown(
    '<div class="section-title">Aktuálne ponuky</div>',
    unsafe_allow_html=True
)


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
    .eq(
        "Status",
        "approved"
    )
    .order(
        "created_at",
        desc=True
    )
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
        f"Počet aktuálnych ponúk: {len(offers)}"
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
            symbol = "●"

        elif offer_type == "Vymením":
            symbol = "↔"

        elif offer_type == "Ponúkam pomoc":
            symbol = "♡"

        else:
            symbol = "•"


        expander_title = (
            f"{symbol}  {offer_type}  |  {title}"
        )


        with st.expander(
            expander_title,
            expanded=False
        ):

            if offer.get(
                "photo_url"
            ):

                st.image(
                    offer[
                        "photo_url"
                    ],
                    width=300
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


            with st.expander(
                "×  Moja ponuka – odstrániť",
                expanded=False
            ):

                st.caption(
                    "Na odstránenie ponuky "
                    "zadajte svoj 6-miestny PIN."
                )


                user_pin = st.text_input(
                    "PIN",
                    type="password",
                    max_chars=6,
                    key=f"pin_{offer['id']}"
                )


                attempts_key = (
                    f"attempts_{offer['id']}"
                )


                if attempts_key not in st.session_state:

                    st.session_state[
                        attempts_key
                    ] = 0


                if st.button(
                    "Odstrániť ponuku",
                    key=f"delete_{offer['id']}"
                ):

                    if (
                        not user_pin.isdigit()
                        or len(user_pin) != 6
                    ):

                        st.warning(
                            "PIN musí obsahovať 6 číslic."
                        )


                    elif (
                        st.session_state[
                            attempts_key
                        ] >= 5
                    ):

                        st.error(
                            "Príliš veľa nesprávnych pokusov."
                        )


                    else:

                        private_response = (
                            admin_supabase
                            .table("Offers")
                            .select(
                                "id,"
                                "photo_url,"
                                "delete_pin_hash"
                            )
                            .eq(
                                "id",
                                offer["id"]
                            )
                            .limit(1)
                            .execute()
                        )


                        if private_response.data:

                            private_offer = (
                                private_response.data[0]
                            )


                            if verify_pin(
                                user_pin,
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

                                st.rerun()


                            else:

                                st.session_state[
                                    attempts_key
                                ] += 1


                                st.error(
                                    "Nesprávny PIN."
                                )


# =========================================================
# ADMINISTRÁCIA
# =========================================================

st.divider()


with st.expander(
    "Administrácia",
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


        st.markdown(
            "### Čakajúce na schválenie"
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

                label = (
                    f"{offer.get('Type', '')} "
                    f"| {offer.get('Title', '')}"
                )


                with st.expander(
                    label,
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


                    col1, col2 = st.columns(2)


                    with col1:

                        if st.button(
                            "Schváliť",
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

                            st.rerun()


                    with col2:

                        if st.button(
                            "Zamietnuť",
                            key=f"reject_{offer['id']}"
                        ):

                            delete_photo(
                                offer.get(
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

                            st.rerun()


        st.markdown(
            "### Aktívne ponuky"
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
                "Žiadne aktívne ponuky."
            )


        else:

            for offer in active_offers:

                label = (
                    f"{offer.get('Type', '')} "
                    f"| {offer.get('Title', '')}"
                )


                with st.expander(
                    label,
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
                        "Vymazať ponuku",
                        key=f"admin_delete_{offer['id']}"
                    ):

                        delete_photo(
                            offer.get(
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

                        st.rerun()


    elif admin_password:

        st.error(
            "Nesprávne admin heslo."
        )
