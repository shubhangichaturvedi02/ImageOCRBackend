from flask import Flask, request, jsonify, make_response,send_file,render_template
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from app import app, db, api
from flask_restful import Resource
from app.models import User, ImageData
import base64
from PIL import Image
import pytesseract
import re
import cv2
import os
import numpy as np

import traceback
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)





UPLOAD_FOLDER = 'images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



   
@app.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    try:
        User.query.filter(User.id == current_user).update({"jwt_token":None}, False)
        return make_response(jsonify({"message":"Logged Out"}), 200)
    except:
        print(traceback.format_exc())
        return make_response(jsonify({"message":"Some Error occured"}), 400)



class Signup(Resource):
    def post(self):
        data = request.json
        print(data)

        if 'name' not in data or 'email' not in data or 'password' not in data:
            return make_response(jsonify({"message": "Missing parameters"}), 400)

        existing_user = User.query.filter(User.email == data['email']).first()
        if existing_user:
            return make_response(jsonify({"message": "User Exists with this email"}), 400)

        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(public_id=str(uuid.uuid4()), name=data['name'], email = data['email'],password=hashed_password, admin=False)

        try:
            db.session.add(new_user)
            db.session.flush()
            user_id = User.id
            db.session.commit()
            user = User.query.filter(User.email == data['email']).first()
            access_token = create_access_token(identity=user.id, fresh=True)
            User.query.filter(User.email == data['email']).update({"jwt_token":access_token},False)
            try:
                db.session.commit()
            except:
                print(traceback.format_exc())
            refresh_token = create_refresh_token(user.id)
            return make_response(jsonify( {
                'access_token': access_token,
                'is_admin': user.admin
            }), 200)
            # return make_response(jsonify({"message": "New user Created Successfully",
            #                                 'access_token': access_token,
            #                             'is_admin': user.admin}), 200)
        except:
            db.session.rollback()
            print(traceback.format_exc())
            return make_response(jsonify({"message": "Some error occured,Please Try later"}), 500)


class userLogin(Resource):
    def post(self):
        data = request.json

        if 'email' not in data or 'password' not in data:
            return make_response(jsonify({"message": "Missing parameters"}), 400)
        
        user = User.query.filter(User.email == data['email']).first()

        if not user:
            return make_response(jsonify({"message": "No User With the given email"}), 400)

        if check_password_hash(user.password, data['password']):
            access_token = create_access_token(identity=user.id, fresh=True)
            User.query.filter(User.email == data['email']).update({"jwt_token":access_token},False)
            try:
                db.session.commit()
            except:
                print(traceback.format_exc())
            refresh_token = create_refresh_token(user.id)
            return make_response(jsonify( {
                'access_token': access_token,
                'is_admin': user.admin
            }), 200)

        return make_response(jsonify({"message": "Invalid credentials"}), 400)


class ImageUpload(Resource):

    def post(self):
        # Check if image file is present in the request
        if 'image' not in request.files:
            return {'message': 'No image file provided'}, 400

        image_file = request.files['image']
        filename = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(filename)

        file_content = image_file.read()
        file_base64 = base64.b64encode(file_content).decode()

        # image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
        # _, img_encoded = cv2.imencode('.png', image)
        # img_base64 = base64.b64encode(img_encoded).decode()

        # bold_text = self.extract_bold_text(filename)
        img = cv2.imread(filename)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to binarize the image
        thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[1]

        # Perform morphological operations to enhance text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        marker = cv2.dilate(thresh, kernel, iterations=1)
        mask = cv2.erode(thresh, kernel, iterations=1)

        while True:
            tmp = marker.copy()
            marker = cv2.erode(marker, None)
            marker = cv2.max(mask, marker)
            difference = cv2.subtract(tmp, marker)
            if cv2.countNonZero(difference) == 0:
                break

        # Perform bitwise OR operation to combine the original image with the marker
        result = cv2.bitwise_or(img, cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR))



        # Use Tesseract OCR to extract text from the result image
        extracted_text_bold = pytesseract.image_to_string(result)

        # Print the extracted text
        print("Extracted Text:")
        print(extracted_text_bold)



        # Convert image to base64
        # image_data = base64.b64encode(image_file.read()).decode('utf-8')


        # Extract text from the image using Tesseract OCR
        extracted_text = self.extract_text_from_image(image_file)

        new_image = ImageData(data=file_base64 , extracted_text=extracted_text, bold_text=extracted_text_bold)
        db.session.add(new_image)
        db.session.commit()


        return {'extracted_text': extracted_text, 'bold_words': extracted_text_bold, 'image_data': file_base64,'name':image_file.filename}

    def extract_text_from_image(self, image_file):
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            return str(e)
    # def preprocess_image(self,image_path):
    #     # Load the image
    #     image = cv2.imread(image_path)
    #
    #     # Convert the image to grayscale
    #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #
    #     # Apply thresholding to binarize the image
    #     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    #
    #     return binary
    #
    # # Function to extract bold text from the preprocessed image
    # def extract_bold_text(self,image_path):
    #     image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    #
    #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #
    #     #Apply thresholding to remove noise and convert the image to binary
    #     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    #
    #     # Set up a marker to dilate the information based on a 5x5 rectangle
    #     kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    #     dilated = cv2.dilate(binary, kernel_dilate, iterations=1)
    #
    #     # Set up a mask to erode the information using a 3x3 rectangle
    #     kernel_erode = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 6))
    #     eroded = cv2.erode(dilated, kernel_erode, iterations=1)
    #     result = cv2.bitwise_and(image, image, mask=eroded)
    #     extracted_text = pytesseract.image_to_string(result)
    #
    #
    #
    #     # Print the extracted text
    #     print("#$$$$$$$$$$$$$$$$$$$$$$$$$",extracted_text)
    #     # Preprocess the image
    #     # binary_image = self.preprocess_image(image_path)
    #     # print(binary_image)
    #     #
    #     # # Use Tesseract OCR to extract text from the image
    #     # extracted_text = pytesseract.image_to_string(binary_image)
    #     # print(extracted_text)
    #     #
    #     # # Split the extracted text into words
    #     # words = extracted_text.split()
    #     #
    #     # # Initialize a list to store bold words
    #     # bold_words = []
    #     #
    #     # # Check if each word is bold
    #     # for word in words:
    #     #     # Check if the word is surrounded by asterisks, indicating bold formatting
    #     #     if word.startswith('**') and word.endswith('**'):
    #     #         bold_words.append(word[2:-2])  # Remove asterisks and add the word to the list of bold words
    #
    #     return extracted_text

    # Path to the image file




    
api.add_resource(Signup,'/signup')
api.add_resource(userLogin,'/login')
api.add_resource(ImageUpload,'/upload')