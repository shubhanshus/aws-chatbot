# aws-chatbot

This repository is part of CloudComputing Assignement 2

Team Members : Khushnaseeb Ali (kk3521), Shubhanshu Surana (ss11012), Vatsal
Shah(vds254), Vaibhav Lodha(vl1015)

Description of important files in the repository:
1.Lambda Code:
  a.Api-lex-lambda.py - lambda function to pass messages back and forth between
  AWS lex from api gateway
  b.SQS-trigger-lambda.py - This is invoked by cloudwatch every miniute and checks
  for messages in sqs, get data from yelp and pushes response into dynamo db
  c.Suggest-restaurant-lambda.py- this is for validation of user information and to
  push the user requirements into SQS queue
