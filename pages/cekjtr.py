import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import numpy as np
from io import StringIO
from io import BytesIO

# Set page configuration to show the sidebar
st.set_page_config(page_title="CekJTR", layout="wide", initial_sidebar_state="expanded")

# Load your authentication configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Re-create the authenticator object to manage logout
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

def find_last_alphabet_position(identifier):
    for i in range(len(identifier) - 1, -1, -1):
        if identifier[i].isalpha():
            return i
    return -1

def split_identifier(identifier, position):
    return identifier[:position].strip()
        
def insert_row(idx, df, new_row):
    dfA = df.iloc[:idx, ]
    dfB = df.iloc[idx:, ]
    df = pd.concat([dfA, new_row, dfB]).reset_index(drop=True)
    return df

def highlight_rows(x):
    df_styler = pd.DataFrame('', index=x.index, columns=x.columns)
    for idx in new_rows_indices:
        df_styler.loc[idx, :] = 'background-color: yellow'
    return df_styler

# Ensure the user is logged in
if 'authentication_status' in st.session_state and st.session_state['authentication_status']:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Line To Path JTR')

    st.write('Upload file dalam bentuk CSV')
    st.write('Pastikan nama kolom : GARDU, SEGMENT JTR, dan NO TIANG')
    st.write('Pastikan terdapat nama kolom. Jika tidak ada bisa dibuat col1, col2, dst')
    st.write('Pastikan isi dari 3 kolom tersebut sesuai dengan contoh format dibawah ini')

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        # To read file as bytes:
        # bytes_data = uploaded_file.read()
        # st.write("filename:", uploaded_file.name)
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, low_memory=False)

        df["Test"] = 1

        coba = []
        i = 0
        new_rows_indices = []

        while i < len(df) - 1:
            if (df.loc[i, "GARDU"] == df.loc[i+1, "GARDU"]):
                if(df.loc[i, "SEGMENT JTR"] != df.loc[i+1, "SEGMENT JTR"]): 
                    target_identifier = df.loc[i+1, "NO TIANG"]
                    last_alpha_pos = find_last_alphabet_position(target_identifier)
                    if last_alpha_pos != -1:
                        splitted_identifier = split_identifier(target_identifier, last_alpha_pos)
                        matched_indices = df.index[df["NO TIANG"] == splitted_identifier].tolist()
                        if matched_indices:
                            last_match_idx = matched_indices[-1]
                            new_row = df.iloc[[last_match_idx]].copy()
                            new_row["SEGMENT JTR"] = df.loc[i+1, "SEGMENT JTR"]
                            new_row["Test"] = 0  # Mark new row with 0 in "Test"
                            coba.append(new_row["NO TIANG"].values[0])
                            df = insert_row(i+1, df, new_row)
                            new_rows_indices.append(i + 1)  # Save the index of the new row
                            i += 1  # Move to the next pair of rows
                        
            i += 1

        df = df.drop_duplicates().reset_index(drop=True)

        # Save to CSV
        df_to_csv = df.to_csv(index=False).encode('utf-8')

        # Applying the highlight using Styler
        styled_df = df.style.apply(highlight_rows, axis=None)

        # Save to Excel
        output_file = 'hasil_'+ uploaded_file.name +".xlsx"
        # df_to_excel=styled_df.to_excel(output_file, index=False, engine='openpyxl')

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            styled_df.to_excel(writer, sheet_name='Result')
        
        st.download_button(label="Download as Excel", data=buffer.getvalue(), file_name=output_file, mime="application/vnd.ms-excel")
        st.download_button("Download as CSV", df_to_csv, 'hasil_'+ uploaded_file.name, "text/csv", key="download-tools-csv")
        # st.download_button("Download Excel", data=styled_df, file_name='hasil_'+ uploaded_file.name +".xlsx", mime='application/octet-stream')

        st.write("Jumlah penambahan node : ", len(coba))
        st.write(coba)

else:
    authenticator.login()