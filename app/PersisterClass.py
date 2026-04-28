import csv 
from VoterClass import Voter
from VoteClass import Vote
from VoteOptionsEnum import VoteOptions
import boto3
import json
from typing import Dict, List
import os

class Persister:
    '''
    Responsible for persisting vote, member, etc data.
    '''

    def __init__(self, use_db=False):
        pass

    def get_vote_log(self,community_board):
        pass

    def add_to_vote_log(self,key,value,community_board):
        pass

    def clear_vote_log(self,community_board):
        pass

    def get_current_vote_name(self,community_board):
        pass

    def set_current_vote_name(self, value,community_board):
        pass

    def get_currently_in_a_voting_session(self,community_board):
        pass

    def set_currently_in_a_voting_session(self, value,community_board):
        pass

    def load_members(self,community_board):
        pass

    def get_members(self,community_board)-> Dict[str, Voter]:
        pass

    def set_members(self, value: Dict[str, Voter],community_board):
        pass

    def get_vote_type(self, community_board: str) -> str:
        pass

    def set_vote_type(self, value: str, community_board: str):
        pass

    def get_election_candidates(self, community_board: str) -> List[str]:
        pass

    def set_election_candidates(self, value: List[str], community_board: str):
        pass

class PersisterBase:
    def list_objects(self, prefix,community_board):
        """
        Lists objects with the given prefix
        Args:
            prefix (str): The prefix to filter objects by
        Returns:
            list: List of object keys matching the prefix
        """
        raise NotImplementedError("Subclass must implement list_objects")

    def get_object(self, key,community_board):
        """
        Gets the content of an object by key
        Args:
            key (str): The key of the object to retrieve
        Returns:
            str: The content of the object
        """
        raise NotImplementedError("Subclass must implement get_object")

class PersisterS3(Persister, PersisterBase):
    '''
    Persister implementation using Amazon S3
    '''

    file_path = '../members.csv'  # TODO this is just for the first launch, remove this

    def __init__(self):
        super().__init__()
        self.s3_resource = boto3.resource('s3')
        self.s3 =  boto3.client('s3')
        self.bucket_name = 'cb7-dashboard-data-store'
        self.vote_log_key = 'vote_log.json'
        self.current_vote_name_key = 'current_vote_name.json'
        self.currently_in_a_voting_session_key = 'currently_in_a_voting_session.json'
        self.members_key = 'members.json'
        self.vote_type_key = 'vote_type.json'
        self.election_candidates_key = 'election_candidates.json'
        self.vote_log_folder = 'vote_log'

    def get_vote_type(self, community_board: str) -> str:
        try:
            obj = self.s3_resource.Object(self.bucket_name, f'/{community_board}/{self.vote_type_key}')
            vote_type_json = obj.get()['Body'].read().decode('utf-8')
            return json.loads(vote_type_json)
        except Exception as e:
            return "RESOLUTION"

    def set_vote_type(self, value: str, community_board: str):
        try:
            obj = self.s3_resource.Object(self.bucket_name, f'/{community_board}/{self.vote_type_key}')
            obj.put(Body=json.dumps(value))
        except Exception as e:
            pass

    def get_election_candidates(self, community_board: str) -> List[str]:
        try:
            obj = self.s3_resource.Object(self.bucket_name, f'/{community_board}/{self.election_candidates_key}')
            election_candidates_json = obj.get()['Body'].read().decode('utf-8')
            return json.loads(election_candidates_json)
        except Exception as e:
            return []

    def set_election_candidates(self, value: List[str], community_board: str):
        try:
            obj = self.s3_resource.Object(self.bucket_name, f'/{community_board}/{self.election_candidates_key}')
            obj.put(Body=json.dumps(value))
        except Exception as e:
            pass

    def get_vote_log(self,community_board) -> Dict[str, Vote]:

        vote_logs = {}

        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.vote_log_folder+'/'+community_board+'/+')
        for obj in response.get('Contents', []):
            # Get the object key (file path)
            object_key = obj['Key']

            # Fetch the object's data
            response = self.s3.get_object(Bucket=self.bucket_name, Key=object_key)
            object_data = response['Body'].read().decode('utf-8')
            # Load the object data as JSON
            try:
                data = json.loads(object_data)
            except json.JSONDecodeError:
                print(f"Error loading JSON for object: {object_key}")
                continue
            
            # Extract data and create the desired object structure
            sms_number = object_key.split('/')[2]
            name_to_set = data['voter']
            vote_data = data['votes_vote']
            if vote_data:
                current_vote_type = self.get_vote_type(community_board)
                if current_vote_type == "ELECTION":
                    vote_logs[sms_number] = Vote(voter=Voter(name=name_to_set, sms_number=sms_number), voters_vote=vote_data)
                else:
                    vote_logs[sms_number] = Vote(voter=Voter(name=name_to_set,sms_number=sms_number), voters_vote=VoteOptions(vote_data))
        
        return vote_logs
        
    def add_to_vote_log(self,key,value,community_board):
        try:
            obj = self.s3_resource.Object(self.bucket_name, self.vote_log_folder+'/'+community_board+'/'+value.voter.sms_number)
            to_save = value.toJSON()
            obj.put(Body=json.dumps(to_save))
        except Exception as e:
            # Handle any exceptions
            pass

    def clear_vote_log(self,community_board):
        # List all objects with the specified prefix
        objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.vote_log_folder+'/'+community_board+'/')

        # Check if the bucket has any objects
        if 'Contents' in objects:
            # Extract the object keys to be deleted
            keys = [{'Key': obj['Key']} for obj in objects['Contents']]

            # Delete the objects in batches for efficiency
            chunk_size = 1000  # You can adjust the chunk size as needed
            for i in range(0, len(keys), chunk_size):
                response = self.s3.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': keys[i:i + chunk_size]}
                )

                # Check if any objects failed to delete
                if 'Errors' in response:
                    for error in response['Errors']:
                        print(f"Error deleting object: {error['Key']} - {error['Message']}")

    def get_current_vote_name(self,community_board):
        # Implement S3-based getter for current_vote_name
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.current_vote_name_key)
            current_vote_name_json = obj.get()['Body'].read().decode('utf-8')
            return json.loads(current_vote_name_json)
        except Exception as e:
            # Handle any exceptions
            return ''

    def set_current_vote_name(self, value,community_board):
        # Implement S3-based setter for current_vote_name
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.current_vote_name_key)
            obj.put(Body=json.dumps(value))
        except Exception as e:
            # Handle any exceptions
            pass

    def get_currently_in_a_voting_session(self,community_board):
        # Implement S3-based getter for currently_in_a_voting_session
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.currently_in_a_voting_session_key)
            currently_in_a_voting_session_json = obj.get()['Body'].read().decode('utf-8')
            return json.loads(currently_in_a_voting_session_json)
        except Exception as e:
            # Handle any exceptions
            return False

    def set_currently_in_a_voting_session(self, value,community_board):
        # Implement S3-based setter for currently_in_a_voting_session
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.currently_in_a_voting_session_key)
            obj.put(Body=json.dumps(value))
        except Exception as e:
            # Handle any exceptions
            pass

    def get_members(self,community_board)-> Dict[str, Voter]:
        # Implement S3-based getter for members
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.members_key)
            members_json = obj.get()['Body'].read().decode('utf-8')
            members_data = json.loads(members_json)
            # Deserialize members_data into a Dict[str, Voter]
            members = {key: Voter(name=voter['name'], sms_number=key) for key, voter in members_data.items()}
            return members
        except Exception as e:
            # Handle any exceptions
            return {}

    def set_members(self, value,community_board):
        # Implement S3-based setter for members
        try:
            obj = self.s3_resource.Object(self.bucket_name, '/'+community_board+'/'+self.members_key)
            value = {key: voter.toJSON() for key, voter in value.items()}
            obj.put(Body=json.dumps(value))
        except Exception as e:
            # Handle any exceptions
            pass

    def load_members(self,community_board):
        self.members = {}
        with open(self.file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                number = row['number']
                self.members[number] = Voter(name, number)
        self.set_members(self.members,community_board)

    def list_objects(self, prefix):
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            print(f"Error listing objects: {str(e)}")
            return []

    def get_object(self, key):
        try:
            print('trying to get '+self.bucket_name+' '+key)
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error getting object: {str(e)}")
            return None

class PersisterGlobalVariables(Persister, PersisterBase):
    '''
    Persister implementation using Global Variables
    '''

    file_path = '../members.csv'
    file_log_folder = '/home/regolith/Downloads/'

    def __init__(self, use_db=False):
        self.use_db = use_db
        self.currently_in_a_voting_session = False
        self.current_vote_name = ''
        self.vote_log = {}
        self.members = {}
        self.vote_type: str = "RESOLUTION"
        self.election_candidates: List[str] = []

    def get_vote_type(self, community_board: str) -> str:
        return self.vote_type

    def set_vote_type(self, value: str, community_board: str):
        self.vote_type = value

    def get_election_candidates(self, community_board: str) -> List[str]:
        return self.election_candidates

    def set_election_candidates(self, value: List[str], community_board: str):
        self.election_candidates = value

    def get_vote_log(self,community_board)-> Dict[str,Vote]:
        return self.vote_log

    def add_to_vote_log(self,key,value,community_board):
        self.vote_log[key] = value

    def clear_vote_log(self,community_board):
        self.vote_log = {}

    def get_current_vote_name(self,community_board):
        return self.current_vote_name

    def set_current_vote_name(self, value,community_board):
        self.current_vote_name = value

    def get_currently_in_a_voting_session(self,community_board):
        return self.currently_in_a_voting_session

    def set_currently_in_a_voting_session(self, value,community_board):
        self.currently_in_a_voting_session = value

    def load_members(self,community_board):
        self.members = {}
        with open(self.file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                number = row['number']
                self.members[number] = Voter(name, number)
        return self.members

    def get_members(self,community_board)-> Dict[str, Voter]:
        return self.members

    def set_members(self, value: Dict[str, Voter],community_board):
        self.members = value

    def list_objects(self, prefix):
        print("Listing objects")
        try:
            # For local storage, we'll look in a specific directory
            local_path = os.path.join(self.file_log_folder, prefix)
            print(f"Local path: {local_path}")
            # Get all files in directory that match the prefix
            matching_files = []
            for root, _, files in os.walk(os.path.dirname(local_path)):
                for file in files:
                    full_path = os.path.join(root, file)
                    key =  full_path[len(self.file_log_folder):]
                    print(f"Checking file: {key}")
                    matching_files.append(key)
            return matching_files
        except Exception as e:
            print(f"Error listing objects: {str(e)}")
            return []

    def get_object(self, key):
        try:
            local_path = self.file_log_folder+key
            if not os.path.exists(local_path):
                return None
            
            with open(local_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error getting object: {str(e)}")
            return None
