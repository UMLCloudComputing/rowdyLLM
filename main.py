from agent import *
import argparse
from dotenv import *
import os

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS = os.getenv("AGENT_ALIAS")

bedrock = boto3.client(
    service_name='bedrock-agent', 
    region_name='us-east-1',
    aws_access_key_id=AWS_ID,
    aws_secret_access_key=AWS_KEY
)


if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description="Manage Bedrock agents.")

    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new agent. Caution: This will override your .env file")
    create_parser.add_argument("--agent_name", required=True, help="Name of the agent to create")

    # Delete subcommand
    delete_parser = subparsers.add_parser("delete", help="Delete an existing agent")
    delete_parser.add_argument("--agent_id", required=True, help="ID of the agent to delete")

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List all agents")

    # Update subcommand
    update_parser = subparsers.add_parser("update", help="Update an existing agent")

    # Test subcommand
    test_parser = subparsers.add_parser("test", help="Test the agent")

    # Parse the arguments
    args = parser.parse_args()

    # Execute based on command

    match args.command:
        case "create":
            create_agent(args.agent_name)
        case "delete":
            delete_agent(args.agent_id)
        case "list":
            list_agents()
        case "update":
            name = bedrock.get_agent(agentId=AGENT_ID)['agent']['agentName']
            update_agent(AGENT_ID, name)
            time.sleep(5)
            update_alias(AGENT_ALIAS, AGENT_ID)
        case "test":
            url = f"https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/{AGENT_ID}/alias/{AGENT_ALIAS}"
            print(f"Test the Agent at {url}")
        case _:
            parser.print_help()
