from aws_cdk import (
    # Duration,
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    Duration,
    CfnOutput
)
from constructs import Construct
import string
import random
import os

from dotenv import load_dotenv
load_dotenv()

class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.agent_name = kwargs.get('agent_name')

        bucket=s3.Bucket(
            self, 
            id="bucket123", 
            bucket_name=f"infobucket{construct_id.lower()}" # Provide a bucket name here
        )

        knowledge_role = iam.CfnRole(self, "KnowledgeBaseRule",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
            policies=[
                {
                    "policyName": "AmazonBedrockAgentPolicy",
                    "policyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "bedrock:InvokeModel",
                                "Resource": "*",
                            },
                            {
                                "Effect": "Allow",
                                "Action": "bedrock:Retrieve",
                                "Resource": "*",
                            },
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "bedrock:ListFoundationModels",
                                    "bedrock:ListCustomModels"
                                ],
                                "Resource": "*"
                            },
                            {
                                "Effect": "Allow",
                                "Action": "secretsmanager:GetSecretValue",
                                "Resource": "*"
                            },
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "s3:GetObject",
                                    "s3:ListBucket",
                                    "s3:PutObject"
                                ],
                                "Resource": "*"
                            },
                        ],
                    },
                }
            ],
            role_name=f"KnowledgeBaseRole_{construct_id}",
        )

        cfn_knowledge_base = bedrock.CfnKnowledgeBase(self, "MyCfnKnowledgeBase",
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
                )
            ),
            name=f"KnowledgeBase{construct_id}",
            role_arn=knowledge_role.attr_arn,
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="PINECONE",
                pinecone_configuration=bedrock.CfnKnowledgeBase.PineconeConfigurationProperty(
                    connection_string=os.getenv("PINECONE_URL"),
                    credentials_secret_arn=os.getenv("PINECONE_API_KEY"),
                    field_mapping=bedrock.CfnKnowledgeBase.PineconeFieldMappingProperty(
                        metadata_field="metadataField",
                        text_field="textField"
                    ),

                    # the properties below are optional
                    namespace="namespace"
                ),
            ),

            # # the properties below are optional
            # description="description",
            # tags={
            #     "tags_key": "tags"
            # }
        )

        cfn_data_source = bedrock.CfnDataSource(self, "MyCfnDataSource",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=bucket.bucket_arn,

                    # the properties below are optional
                    # bucket_owner_account_id="bucketOwnerAccountId",
                    # inclusion_prefixes=["inclusionPrefixes"]
                ),
                type="S3"
            ),
            knowledge_base_id=cfn_knowledge_base.attr_knowledge_base_id,
            name=f"source{construct_id}",

            # # the properties below are optional
            # data_deletion_policy="dataDeletionPolicy",
            # description="description",
            # server_side_encryption_configuration=bedrock.CfnDataSource.ServerSideEncryptionConfigurationProperty(
            #     kms_key_arn="kmsKeyArn"
            # ),
            # vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
            #     chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
            #         chunking_strategy="chunkingStrategy",

            #         # the properties below are optional
            #         fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
            #             max_tokens=123,
            #             overlap_percentage=123
            #         )
            #     )
            # )
        )

        CfnOutput(self, "Knowledge Base ID: ", value=cfn_knowledge_base.attr_knowledge_base_id)



        