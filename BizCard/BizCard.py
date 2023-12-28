import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import pymysql
import cv2
import os
import re

# MySQL connection
mysql_connection  =  pymysql.connect(host = "127.0.0.1",
                                user='root',
                                passwd='Nisha@130899',
                                database ="BusinessCardData",
                                autocommit=True)                                
mysql_cursor  = mysql_connection.cursor()

#Creating Table in SQL:
mysql_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS business_cards  (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                                                    card_holder TEXT,
                                                                    company_name TEXT,
                                                                    designation TEXT,
                                                                    mobile_number TEXT,
                                                                    email TEXT,
                                                                    website TEXT,
                                                                    area TEXT,
                                                                    city TEXT,
                                                                    state TEXT,
                                                                    pin_code TEXT
                                                                    )
          ''')

mysql_connection.commit()


def get_data(res):
        for ind, i in enumerate(res):

                # To get WEBSITE_URL
                if "www" in i.lower() or "www." in i.lower():
                        data["website"].append(i)
                elif "WWW" in i:
                        data["website"] = res[4] + "." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME
                elif ind == len(res) - 1:
                    #if res[ind-1].isdigit()==False:
                    data["company_name"].append(i)
 
                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                # To get PINCODE
                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])
                #st.write(i)
        df = pd.DataFrame(data)
        return df

def insert_data():
        for index, row in df.iterrows():
                insert_query = '''
                        INSERT INTO business_cards (card_holder, company_name, designation, mobile_number, 
                        email, website, area, city, state, pin_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                '''
                values = (
                        row['card_holder'],
                        row['company_name'],
                        row['designation'],
                        row['mobile_number'],
                        row['email'],
                        row['website'],
                        row['area'],
                        row['city'],
                        row['state'],
                        row['pin_code']
                )
                mysql_cursor.execute(insert_query,values)
        mysql_connection.commit() 

def show_data(data):
        mysql_cursor.execute('''select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from business_cards''')
        columns = [desc[0] for desc in mysql_cursor.description]
        df = pd.DataFrame(data, columns=columns)
        labels_order = ["card_holder", "designation", "company_name", "area", "city", "state", "pin_code", "mobile_number", "email", "website"]
        st.title("Business Card Information")
        for index, row in df.iterrows():
           for label in labels_order:
                st.write(f"**{label.capitalize()}**: {row[label]}")
def fetch_data():
    mysql_cursor.execute('SELECT * FROM business_cards')
    rows = mysql_cursor.fetchall()
    column_names = [desc[0] for desc in mysql_cursor.description]
    data_dict = {}
    for row in rows:
        card_holder_name = row[1]
        data_dict[card_holder_name] = list(row)
    return  data_dict, column_names

# Function to update data in MySQL:
def update_data(selected_option, updated_values, column_names):
    update_query = f"UPDATE business_cards SET {','.join([f'{column_name} = %s' for column_name in column_names])} WHERE card_holder = %s"
    mysql_cursor.execute(update_query, updated_values + [selected_option])
    mysql_connection.commit()

def delete_data():
        delete_query = "DELETE FROM business_cards WHERE card_holder = %s"
        mysql_cursor.execute(delete_query, [selected_option])
        mysql_connection.commit()

# Page Config:       
st.set_page_config(page_title="BizCardX: Extracting Business Card Data with OCR",                   
                   layout="wide",
                   initial_sidebar_state="expanded")
# Sidebar
st.sidebar.header(("About"))
st.sidebar.write(("Technologies Used :"))
st.sidebar.markdown("""
    <div style="margin-left: 40px;">
       <ul>
            <li>Python</li>
            <li>easy OCR</li>
            <li>Streamlit</li>
            <li>SQL</li>
            <li>Pandas</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# Streamlit:

selected = option_menu(None, ["Home","Upload & Extract","Modify"], 
                       icons=["home","cloud-upload-alt","edit"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "25px", "text-align": "centre", "margin": "0px", "--hover-color": "#000080", "transition": "color 0.3s ease, background-color 0.3s ease"},
                               "icon": {"font-size": "25px"},
                               "container" : {"max-width": "6000px", "padding": "10px", "border-radius": "5px"},
                               "nav-link-selected": {"background-color": "#000080", "color": "white"}})
reader = easyocr.Reader(['en'])

if selected == "Home":
    st.markdown("<h1 style='text-align: center; color: DodgerBlue;'>The most versatile Business Card Scanner</h1>",
        unsafe_allow_html=True)
    st.markdown("<div style='font-family: Arial, sans-serif; text-align: center;'>Convert any Image of a business card into Excel (XLS), CSV or JSON formats.</div>",
                unsafe_allow_html=True)    
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.header("1")
        st.subheader("Add Business Card")
        st.markdown("Select the file from your computer, or just drag and drop into the upload box. We also support images of driver's licenses!")
    with c2:
        st.header("2")
        st.subheader("Scan Business Card")
        st.markdown("Our converter automatically recognises all the data in your business card regardless of its format.")
    with c3:
        st.header("3")
        st.subheader("Modify or Update")
        st.markdown("Update the data and delete the data through the streamlit UI")

if selected == "Upload & Extract":
    uploaded_card = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])
    
    if uploaded_card is not None:
                with st.spinner("Please wait processing image..."):
                        uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
                        os.makedirs(uploaded_cards_dir, exist_ok=True)  # Create the directory if it doesn't exist
                        with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
                                f.write(uploaded_card.getbuffer())
                        
                        
                        st.set_option('deprecation.showPyplotGlobalUse', False)
                        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
                        image = cv2.imread(saved_img)
                        res = reader.readtext(saved_img)               
                        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
                        result = reader.readtext(saved_img, detail=0, paragraph=False)

                        data = {"card_holder": [],
                                "company_name": [],
                                "designation": [],
                                "mobile_number": [],
                                "email": [],
                                "website": [],
                                "area": [],
                                "city": [],
                                "state": [],
                                "pin_code": []
                                }
                        
                st.markdown("### Image Processed and Data Extracted") 
                df=get_data(result)
                c1,c2,c3 = st.columns(3)
                with c1:
                   st.image(image)
                with c3:
                      for index, row in df.iterrows():
                        st.write(f"Card Holder: {row['card_holder']}")
                        st.write(f"Company Name: {row['company_name']}")
                        st.write(f"Designation: {row['designation']}")
                        st.write(f"Mobile Number: {row['mobile_number']}")
                        st.write(f"Email: {row['email']}")
                        st.write(f"Website: {row['website']}")
                        st.write(f"Area: {row['area']}")
                        st.write(f"City: {row['city']}")
                        st.write(f"State: {row['state']}")
                        st.write(f"Pin Code: {row['pin_code']}")
                if st.button("Upload to Database"):
                    with st.spinner("Please wait while Uploading..."):
                        insert_data()
                        st.text("Data Uploaded Successfully.")
                        show_data(data)
if selected == "Modify":
      # Connect to MYSQL and fetch data
        data, column_names = fetch_data()
        card_holder_names = [entry[1] for entry in data.values()]
        # Create a dropdown box and populate it with the card holders
        selected_option = st.selectbox("Select a card holder:", ["None"] + card_holder_names)

        tab1, tab2 = st.tabs(["Edit The Data", "Delete The Data"])
        with tab1:
        # Display text boxes for each column of the selected card holder
            if selected_option != "None":
                    st.write("You selected:", selected_option)
                    if selected_option in data:
                            st.write("Modify the data:")
                            updated_values = list(data[selected_option])  # Create a list of the original values
                            
                            for i, column_name in enumerate(column_names):
                                    new_value = st.text_input(column_name, data[selected_option][i])
                                    updated_values[i] = new_value  # Update the corresponding value
                                    st.write(f"Updated {column_name}: {new_value}")
                
                            # Add a button to save the updated data
                            if st.button("Update"):
                                    update_data(selected_option, updated_values, column_names)
                                    mysql_connection.commit()
                                    st.success("Data has been updated.")

                    else:
                            st.write("Option not found in data.")
            else:
                    st.write("No card holder selected.")

        with tab2:
            if selected_option != "None":
                    st.write("You selected:", selected_option)
                    if selected_option in data:
                            query = 'SELECT * FROM business_cards WHERE card_holder = %s'
                            mysql_cursor.execute(query, (selected_option,))
                            df = mysql_cursor.fetchall()
                            st.write(pd.DataFrame(df, columns=['id','Card Holder','Company Name', 'Designation','Mobile Number', 'Email', 
                                                                    'Website', 'Area', 'City','State', 'Pin Code']))
                            mysql_connection.commit()
                            st.write("The Data Of This Card Holder Will Be Deleted")
                    if st.button("Delete"):
                            delete_data()
                            st.success("Data Successfully deleted!!")