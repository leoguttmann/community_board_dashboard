TODO

* Cb cors issue

# Run it all local

change the persister to Global Variable and the Logger
export FLASK_APP=flask_app.py
export API_KEY=auth-key-value
cd /app
flask run --reload
http://127.0.0.1:5000/webresults



# deploy hosted
sh deploy_lambda.sh 


# AWS Setup

API Gateway - setup endpoints
Lambda - create with the attached script, comment out the create


# create the twilio_layer
mkdir python
cd python
vim requirements.txt add urllib3<2 and twilio
pip3 install -r requirements.txt -t ./
zip -r python.zip . (STOP, there must be a python/ when you first unzip so nest another python folder or change zip)
In the AWS Lambda console, navigate to the "Layers" section. Click the "Create layer" button, and then:

Enter a name for your layer.
Provide a description (optional).
Upload the python.zip file.
Choose a compatible runtime (e.g., Python 3.8 or the runtime you intend to use).
Click "Create" to create the Lambda layer.

# Lambda permissions
aws lambda add-permission --function-name CBFunction --statement-id apigateway-invoke-permissions --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:accound:lambda/default/GET/test"

# AUTH
* For twilio, a parameter is added to the url string in twilio config
* For lambda and local flask, environment variable is being checked vs x-api-key

# python scrip to upload members.csv to s3 as members.json
python3 uploadmembers.py


TWILIO setup before

https://b9p8ybxhj7.execute-api.us-east-1.amazonaws.com/default/incomingtext?auth=XYZ

now

https://cb.labsbell.com/default/incomingtext?auth=XYZ&cb=7