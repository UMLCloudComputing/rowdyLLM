
# Welcome to the RowdyLLM project!

This is a subproject of RowdyBot, that attempts to separate out the LLM component of Rowdybot, due to the inherent complexities of setting up Amazon Bedrock Agents.
The goal of this project is to allow the developer to setup the Amazon Bedrock Agent with just one command.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

Install the requirements for this project here.
```
$ pip install -r requirements.txt
```



## Setup
Now you need to setup the proper environmental variables. This can be done by creating a .env file in your root directory.
As of now, the only two you need are the Pinecone Vector Index, API Key, and the name of your CloudFormation Stack.

First you need to create a Pinecone Vector Index. Copy out the Vector Database URL and paste in the the .env file.
The Pinecone API Key must be stored in the AWS Secrets Manager with the keyname as "apiKey" and the secret value as your pinecone API Key. Paste the ARN of the secret in the .env file.

You can name your APP_NAME whatever you wish, but be careful not to nameclash with your teammates' cloudformation app names.
```
PINECONE_URL = <Pinecone Vector Database URL>
PINECONE_API_KEY = <ARN of AWS Secret that store your Pinecone API Key>
APP_NAME=<Cloudformation App Name>
```

At this point you can deploy through these commands

```
$ cdk bootstrap
$ cdk deploy
```

## Running the Streamlit App
After deployment you should get this at the bottom of the output.
```
Outputs:
CdkStack1.KnowledgeBaseID = .......
Stack ARN:
....
```

Copy the KnowledgeBaseID and paste it in the `.streamlit/secrets.toml` file as the value of the KB_ID variable like this

```
KB_ID = "......."
```

Make sure to also save your AWS Credentials in the `.streamlit/secrets.toml` file as well.

```
AWS_ACCESS_KEY_ID = "......."
AWS_SECRET_ACCESS_KEY = "......."
```

Finally, run `streamlit run rowdy_stream.py` to start the streamlit app. The output will tell you the local address to access the app.


## Additional Dependencies
To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
