from datetime import datetime
import boto3
import pytz
import os

class VoteLoggingClass:
    '''
    Responsible for logging raw and summary votes
    '''
    def get_day_for_timestamp(self):
        eastern = pytz.timezone('America/New_York')
        today = datetime.now(eastern)
        formatted_date = today.strftime("%Y_%m_%d")
        return formatted_date

    def get_time_stamp_with_seconds(self):
        eastern = pytz.timezone('America/New_York')
        today = datetime.now(eastern)
        formatted_date = today.strftime("%Y_%m_%d_%H:%M:%S")
        return formatted_date

    def __init__(self):
        pass

    def log_raw_vote_to_file(self, incoming_number,incoming_msg,current_vote_name,community_board):
        pass

    def log_vote_summary_to_file(self,current_vote_name,summary,community_board):
        pass

class LocalVoteLoggingClass(VoteLoggingClass):
    file_log_folder = '/home/regolith/Downloads/'

    def __init__(self):
        pass

    def log_raw_vote_to_file(self, incoming_number: str, incoming_msg: str, current_vote_name: str,community_board:str) -> None:
        f = open(self.file_log_folder+'/vote_log'+community_board+ self.get_day_for_timestamp() +'.txt', "a")
        f.write(self.get_time_stamp_with_seconds()+','+incoming_number+','+incoming_msg+','+current_vote_name+'\n')
        f.close()

    def log_vote_summary_to_file(self,current_vote_name,summary,community_board):
        directory = os.path.join(self.file_log_folder, 'summaryvotelog', community_board)
        os.makedirs(directory, exist_ok=True)
        f = open(os.path.join(directory, self.get_day_for_timestamp() + '.txt'), "a")
        f.write(summary)
        f.close()


class S3VoteLoggingClass(VoteLoggingClass):
    def __init__(self):
        self.s3_resource = boto3.resource('s3')
        self.bucket_name = 'qcb2-dashboard-data-store'
        self.vote_summary_folder = 'summaryvotelog/'
        self.vote_raw_folder = 'rawvotelog/'

    def log_raw_vote_to_file(self, incoming_number: str, incoming_msg: str, current_vote_name: str,community_board:str) -> None:
        try:
            object_key = self.vote_raw_folder + community_board + '/' + self.get_time_stamp_with_seconds()+'_'+incoming_number + '.txt'
            obj = self.s3_resource.Object(self.bucket_name, object_key)
            value = self.get_time_stamp_with_seconds()+','+incoming_number+','+incoming_msg+','+current_vote_name+'\n'
            obj.put(Body=value)
        except Exception as e:
            # Handle any exceptions
            pass

    def log_vote_summary_to_file(self,current_vote_name, summary,community_board:str):
        try:
            object_key = self.vote_summary_folder + community_board + '/' + self.get_day_for_timestamp()+'_'+current_vote_name+'_summary.txt'
            obj = self.s3_resource.Object(self.bucket_name, object_key)
            obj.put(Body=summary)
        except Exception as e:
            # Handle any exceptions
            pass
