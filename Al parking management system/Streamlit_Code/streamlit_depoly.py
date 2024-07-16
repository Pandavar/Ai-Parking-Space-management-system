# Import necessary libraries
import easyocr  # OCR library to read text from images
import cv2  # OpenCV library for computer vision tasks
import pytesseract  # Tesseract OCR engine
import re  # Regular expressions for pattern matching
import time  # Time-related functions
from datetime import datetime  # Module to handle date and time
import numpy as np  # Numerical operations
import pandas as pd  # Data manipulation and analysis
import matplotlib.pyplot as plt  # Plotting library
import streamlit as st  # Web app framework
from sql_connection import connect_to_db, insert_entry, update_entry, calculate_parking_fee  # Custom SQL functions
import os  # Operating system interface
import psycopg2  # PostgreSQL database adapter

# Set the path for Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize EasyOCR reader with English language
reader = easyocr.Reader(['en'], gpu=False)

# Load the Haar Cascade for number plate detection
numplate_cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')

# Function to extract the number plate from a frame
def extract_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to grayscale
    edges = cv2.Canny(gray, 50, 150)  # Detect edges in the grayscale image
    sharpened_image2 = cv2.GaussianBlur(gray, (7, 7), 0)  # Sharpen the image using GaussianBlur
    num_plate = numplate_cascade.detectMultiScale(sharpened_image2, minNeighbors=10)  # Detect number plates
    if len(num_plate) > 0:
        W, H, w, h = num_plate[0]  # Get the coordinates of the detected plate
        cv2.rectangle(frame, (W, H), (W+w, H+h), (0, 0, 200), 2)  # Draw a rectangle around the plate
        plate = frame[H:H+h, W:W+w]  # Extract the plate from the frame
        plt.imshow(plate)  # Display the plate
        plt.show()
        return plate  # Return the extracted plate
    else:
        return None  # Return None if no plate is detected

# Function to remove spaces and convert to uppercase
def upper_strip(num_plate):
    return ''.join(num_plate.split()).upper()

# Function to extract the registration number from a plate
def extract_number(plate):
    # Use EasyOCR to read text from the plate
    reg_num = reader.readtext(plate, detail=0)
    print(reg_num)
    pattern = r'^[A-Z]{2}.*[0-9]{1,4}$'  # Pattern to match registration numbers
    matches = []
    for i in reg_num:
        match = re.findall(pattern, upper_strip(i))  # Find matches in the extracted text
        if match:
            matches.extend(match)
    if matches:
        return matches[0]  # Return the first match
    else:
        return None  # Return None if no matches are found

# Function to fetch data from the database
def fetch_data():
    conn = connect_to_db()  # Connect to the database
    if conn:
        try:
            cursor = conn.cursor()
            fetch_query = '''
                SELECT * FROM number_plate_details;
            '''  # SQL query to fetch data
            cursor.execute(fetch_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)  # Convert to DataFrame
            return df  # Return the DataFrame
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()  # Close the cursor
            conn.close()  # Close the connection
    return pd.DataFrame()  # Return empty DataFrame if there's an error

# Dictionary to keep track of plate entry times
plate_entry_times = {}

# Main function to run the Streamlit app
def main():
    st.title("Parking Lot Management System")  # Set the title of the app
    
    # Define the path to the video file
    video_path = r'd:\Deep Learning\OCR(Object_character_recognition)\WhatsApp Video 2024-06-28 at 11.48.16_00aa7520.mp4'
    
    # Open the video file using OpenCV
    cap = cv2.VideoCapture(video_path)
    count = 0  # Initialize the frame count

    # Create a frame window in Streamlit to display video frames
    frame_window = st.image([])
    
    # Create a button in Streamlit to stop the video processing
    y = st.button('stop')

    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        
        # If no frame is returned, exit the loop
        if not ret:
            break
        
        # Resize the frame to half its original size
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        # Extract the number plate from the frame
        number_plate = extract_plate(frame)
        entry_id = None
        timestamp_entering = None

        if number_plate is not None:
            # Extract the registration number from the number plate
            reg_num = extract_number(number_plate)
            
            # Overlay the registration number on the frame
            cv2.putText(frame, f'{reg_num}', (100, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (0, 0, 200), 2)
            
            # Every 10 frames, perform the following actions
            if count % 10 == 0:
                print(f"Frame count {count}")
                
                # If a registration number is extracted
                if reg_num:
                    # If the registration number is not already logged
                    if reg_num not in plate_entry_times.keys():
                        # Record the entry timestamp
                        timestamp_entering = datetime.now()
                        
                        # Insert entry details into the database and get the entry ID
                        entry_id = insert_entry(reg_num, timestamp_entering)
                        
                        # Store the entry timestamp in the dictionary
                        plate_entry_times[reg_num] = datetime.now()
                    
                    # If an entry ID exists (i.e., the car was logged in)
                    if entry_id is not None:
                        # Record the exit timestamp
                        timestamp_leaving = datetime.now()
                        
                        # Calculate the time taken for parking
                        time_taken = timestamp_leaving - timestamp_entering
                        
                        # Calculate the parking fee based on entry and exit times
                        parking_fee = calculate_parking_fee(timestamp_entering, timestamp_leaving)
                        
                        # Update the database with exit details
                        update_entry(entry_id, timestamp_leaving, time_taken, parking_fee)
                        
                        # Remove the registration number from the dictionary
                        del plate_entry_times[reg_num]
                        
        count += 1  # Increment the frame count
        
        # Display the frame with the overlayed registration number in the Streamlit app
        frame_window.image(frame, channels="BGR")
        
        # Exit the loop if the 'stop' button is pressed
        if y:
            break

    # Release the video capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

    # Fetch and display the data from the database
    data = fetch_data()
    if not data.empty:
        st.subheader("Parking Lot Data")  # Subheader for the data section
        st.write(data)  # Display the data in the Streamlit app

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
